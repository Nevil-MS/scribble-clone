from __future__ import annotations

import uuid
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from ..game.game import Game
from ..game.engine import GameEngine
from ..game.state import GameState
from ..models.player import Player
from ..models.gamesettings import GameSettings

from .messages import (
    ClientMessage,
    ServerMessage,
    chat_message,
    error_message,
    player_joined,
    player_left,
    system_message,
    game_state_message,
)
from .websocket import ConnectionManager


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Game] = {}

    def create_room(
        self,
        settings: GameSettings,
    ) -> Game:
        room_id = settings.room_id

        game = Game(
            room_id=room_id,
            state=GameState.LOBBY,
            settings=settings,
        )

        self.rooms[room_id] = game

        return game

    def get_room(self, room_id: str) -> Game | None:
        return self.rooms.get(room_id)

    def remove_room(self, room_id: str):
        self.rooms.pop(room_id, None)


room_manager = RoomManager()
connection_manager = ConnectionManager()


def generate_pid() -> str:
    return str(uuid.uuid4())


def generate_room_id() -> str:
    return uuid.uuid4().hex[:6].upper()


def serialize_player(
    player: Player,
) -> dict[str, Any]:
    return {
        "pid": player.pid,
        "name": player.name,
        "avatar": player.avatar,
        "room_id": player.room_id,
        "connected": player.connected,
    }


def serialize_players(
    game: Game,
) -> list[dict[str, Any]]:
    return [
        serialize_player(player)
        for player in game.players.values()
    ]


def serialize_settings(
    settings: GameSettings,
) -> dict[str, Any]:
    return {
        "room_id": settings.room_id,
        "player_count": settings.player_count,
        "language": settings.language,
        "draw_time": settings.draw_time,
        "rounds": settings.rounds,
        "word_count": settings.word_count,
        "hints": settings.hints,
        "custom_words": settings.custom_words,
        "custom_words_only": settings.custom_words_only,
    }


def serialize_game_state(
    game: Game,
) -> dict[str, Any]:
    current_turn = game.current_turn

    current_drawer = None

    if current_turn is not None:
        current_drawer = getattr(
            current_turn,
            "drawer_pid",
            getattr(current_turn, "drawer_id", None),
        )

    return {
        "room_id": game.room_id,
        "state": (
            game.state.value
            if hasattr(game.state, "value")
            else str(game.state)
        ),
        "players": serialize_players(game),
        "connected_players": list(game.connected_players),
        "settings": serialize_settings(game.settings),
        "current_drawer": current_drawer,
        "current_round": (
            game.current_round.round_number
            if (
                game.current_round is not None
                and hasattr(
                    game.current_round,
                    "round_number",
                )
            )
            else None
        ),
    }


async def send_game_state(
    game: Game,
):
    message = ServerMessage(
        type="game_state",
        data=serialize_game_state(game),
    ).to_dict()

    await connection_manager.send_to_players(
        game.connected_players,
        message,
    )


async def send_error(
    pid: str,
    message: str,
):
    await connection_manager.send_to_player(
        pid,
        error_message(message),
    )


async def handle_join(
    game: Game,
    pid: str,
    data: dict[str, Any],
):
    name = str(
        data.get("name", "")
    ).strip()

    if not name:
        name = f"Player-{pid[:6]}"

    avatar = data.get("avatar")

    if not avatar:
        avatar = f"avatar-{pid[:6]}"

    if pid in game.players:
        player = game.players[pid]

        player.connected = True
        player.room_id = game.room_id

    else:
        player = Player(
            pid=pid,
            name=name,
            avatar=avatar,
            room_id=game.room_id,
            connected=True,
        )

        game.players[pid] = player

    game.connected_players.add(pid)

    await connection_manager.send_to_player(
        pid,
        player_joined(
            serialize_player(player)
        ),
    )

    await connection_manager.send_to_player(
        pid,
        ServerMessage(
            type="game_state",
            data=serialize_game_state(game),
        ).to_dict(),
    )

    await connection_manager.send_to_players(
        game.connected_players - {pid},
        player_joined(
            serialize_player(player)
        ),
    )


async def handle_reconnect(
    game: Game,
    pid: str,
):
    player = game.players.get(pid)

    if player is None:
        await send_error(
            pid,
            "Player does not exist in this room.",
        )
        return

    player.connected = True
    player.room_id = game.room_id

    game.connected_players.add(pid)

    await connection_manager.send_to_player(
        pid,
        ServerMessage(
            type="game_state",
            data=serialize_game_state(game),
        ).to_dict(),
    )

    await connection_manager.send_to_players(
        game.connected_players - {pid},
        system_message(
            f"{player.name} reconnected."
        ),
    )


async def handle_chat(
    game: Game,
    pid: str,
    data: dict[str, Any],
):
    player = game.players.get(pid)

    if player is None:
        await send_error(
            pid,
            "Player not found.",
        )
        return

    message = str(
        data.get("message", "")
    ).strip()

    if not message:
        return

    result = game_engine(
        game
    ).process_guess(
        pid,
        message,
    )

    if result == "CHAT":
        game_engine(game).add_chat_message(
            pid,
            message,
        )

        await connection_manager.send_to_players(
            game.connected_players,
            chat_message(
                pid,
                player.name,
                message,
            ),
        )

    elif result == "CORRECT":
        await handle_correct_guess(
            game,
            pid,
            player.name,
        )

    elif result == "CLOSE":
        game_engine(game).add_chat_message(
            pid,
            message,
        )

        await connection_manager.send_to_players(
            game.connected_players,
            chat_message(
                pid,
                player.name,
                message,
            ),
        )

        await connection_manager.send_to_player(
            pid,
            system_message(
                "Your guess is close!"
            ),
        )

    elif result == "WRONG":
        game_engine(game).add_chat_message(
            pid,
            message,
        )

        await connection_manager.send_to_players(
            game.connected_players,
            chat_message(
                pid,
                player.name,
                message,
            ),
        )

    elif isinstance(result, dict):
        await handle_correct_guess(
            game,
            pid,
            player.name,
            turn_end_result=result,
        )

    else:
        await send_error(
            pid,
            "Invalid guess result.",
        )


async def handle_correct_guess(
    game: Game,
    pid: str,
    player_name: str,
    turn_end_result: dict[str, Any] | None = None,
):
    await connection_manager.send_to_player(
        pid,
        system_message(
            "Correct guess!"
        ),
    )

    other_players = (
        game.connected_players - {pid}
    )

    await connection_manager.send_to_players(
        other_players,
        system_message(
            f"{player_name} guessed correctly!"
        ),
    )

    if turn_end_result is None:
        if game_engine(
            game
        ).all_guessers_correct():
            turn_end_result = game_engine(
                game
            ).end_turn(
                "ALL_GUESSERS_CORRECT"
            )

    if turn_end_result is not None:
        await connection_manager.send_to_players(
            game.connected_players,
            ServerMessage(
                type="game_state",
                data={
                    "event": "turn_end",
                    **turn_end_result,
                },
            ).to_dict(),
        )

        await send_game_state(game)


async def handle_select_word(
    game: Game,
    pid: str,
    data: dict[str, Any],
):
    current_turn = game.current_turn

    if current_turn is None:
        await send_error(
            pid,
            "There is no active turn.",
        )
        return

    drawer_pid = getattr(
        current_turn,
        "drawer_pid",
        getattr(
            current_turn,
            "drawer_id",
            None,
        ),
    )

    if pid != drawer_pid:
        await send_error(
            pid,
            "Only the drawer can select a word.",
        )
        return

    word_id = data.get("word_id")

    if word_id is None:
        await send_error(
            pid,
            "word_id is required.",
        )
        return

    try:
        game_engine(game).select_word(
            word_id
        )

    except Exception as exc:
        await send_error(
            pid,
            str(exc),
        )
        return

    await broadcast_selected_word(game)

    await send_game_state(game)


async def broadcast_selected_word(
    game: Game,
):
    current_turn = game.current_turn

    if current_turn is None:
        return

    drawer_pid = getattr(
        current_turn,
        "drawer_pid",
        getattr(
            current_turn,
            "drawer_id",
            None,
        ),
    )

    selected_word = getattr(
        current_turn,
        "word",
        None,
    )

    if selected_word is None:
        selected_word = getattr(
            current_turn,
            "selected_word",
            None,
        )

    for pid in game.connected_players:

        if pid == drawer_pid:
            await connection_manager.send_to_player(
                pid,
                ServerMessage(
                    type="game_state",
                    data={
                        "event": "word_selected",
                        "word": selected_word,
                    },
                ).to_dict(),
            )

        else:
            await connection_manager.send_to_player(
                pid,
                ServerMessage(
                    type="game_state",
                    data={
                        "event": "word_selected",
                        "word": None,
                    },
                ).to_dict(),
            )


async def handle_draw(
    game: Game,
    pid: str,
    data: dict[str, Any],
):
    current_turn = game.current_turn

    if current_turn is None:
        await send_error(
            pid,
            "There is no active turn.",
        )
        return

    drawer_pid = getattr(
        current_turn,
        "drawer_pid",
        getattr(
            current_turn,
            "drawer_id",
            None,
        ),
    )

    if pid != drawer_pid:
        await send_error(
            pid,
            "Only the drawer can draw.",
        )
        return

    drawing_message = ServerMessage(
        type="draw",
        data={
            "pid": pid,
            **data,
        },
    ).to_dict()

    await connection_manager.send_to_players(
        game.connected_players - {pid},
        drawing_message,
    )


async def handle_lobby_update(
    game: Game,
    pid: str,
    data: dict[str, Any],
):
    players = game.players

    if not players:
        await send_error(
            pid,
            "No players in the room.",
        )
        return

    host_pid = next(
        iter(players.keys())
    )

    if pid != host_pid:
        await send_error(
            pid,
            "Only the host can update lobby settings.",
        )
        return

    settings = game.settings

    allowed_fields = {
        "player_count",
        "language",
        "draw_time",
        "rounds",
        "word_count",
        "hints",
        "custom_words",
        "custom_words_only",
    }

    for field_name in allowed_fields:
        if field_name in data:
            setattr(
                settings,
                field_name,
                data[field_name],
            )

    await send_game_state(game)


async def handle_start_game(
    game: Game,
    pid: str,
):
    players = game.players

    if not players:
        await send_error(
            pid,
            "No players in the room.",
        )
        return

    host_pid = next(
        iter(players.keys())
    )

    if pid != host_pid:
        await send_error(
            pid,
            "Only the host can start the game.",
        )
        return

    if (
        len(game.connected_players)
        < game.settings.player_count
    ):
        await send_error(
            pid,
            "Not enough players to start the game.",
        )
        return

    try:
        game_engine(game).start_game()

    except Exception as exc:
        await send_error(
            pid,
            str(exc),
        )
        return

    await send_game_state(game)


async def handle_message(
    game: Game,
    pid: str,
    message: dict[str, Any],
):
    client_message = ClientMessage.from_dict(
        message
    )

    message_type = client_message.type
    data = client_message.data

    if message_type == "join":
        await handle_join(
            game,
            pid,
            data,
        )

    elif message_type == "chat":
        await handle_chat(
            game,
            pid,
            data,
        )

    elif message_type == "select_word":
        await handle_select_word(
            game,
            pid,
            data,
        )

    elif message_type == "draw":
        await handle_draw(
            game,
            pid,
            data,
        )

    elif message_type == "lobby_update":
        await handle_lobby_update(
            game,
            pid,
            data,
        )

    elif message_type == "start_game":
        await handle_start_game(
            game,
            pid,
        )

    elif message_type == "reconnect":
        await handle_reconnect(
            game,
            pid,
        )

    else:
        await send_error(
            pid,
            f"Unknown message type: {message_type}",
        )


def game_engine(
    game: Game,
) -> GameEngine:
    return GameEngine(game)


async def handle_disconnect(
    game: Game,
    pid: str,
):
    player = game.players.get(pid)

    game.connected_players.discard(pid)

    if player is not None:
        player.connected = False

        await connection_manager.send_to_players(
            game.connected_players,
            player_left(pid),
        )

    if pid in game.players:
        result = game_engine(
            game
        ).handle_disconnect(pid)

        if result == "GAME_END":
            await connection_manager.send_to_players(
                game.connected_players,
                system_message(
                    "Game ended because too few players remain."
                ),
            )

        elif result == "DRAWER_DISCONNECTED":
            await connection_manager.send_to_players(
                game.connected_players,
                system_message(
                    "The drawer disconnected."
                ),
            )

        elif result == "GUESSER_DISCONNECTED":
            await connection_manager.send_to_players(
                game.connected_players,
                system_message(
                    "All remaining guessers are correct."
                ),
            )

        await send_game_state(game)


async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
):
    pid = websocket.query_params.get(
        "pid"
    )

    if not pid:
        pid = generate_pid()

    game = room_manager.get_room(
        room_id
    )

    if game is None:
        await websocket.accept()

        await websocket.send_json(
            error_message(
                "Room not found."
            )
        )

        await websocket.close()
        return

    await connection_manager.connect(
        pid,
        websocket,
    )

    try:
        await websocket.send_json(
            ServerMessage(
                type="connection",
                data={
                    "pid": pid,
                    "room_id": room_id,
                },
            ).to_dict()
        )

        while True:
            message = await websocket.receive_json()

            await handle_message(
                game,
                pid,
                message,
            )

    except WebSocketDisconnect:
        pass

    finally:
        connection_manager.disconnect(
            pid
        )

        await handle_disconnect(
            game,
            pid,
        )