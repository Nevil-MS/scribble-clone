from __future__ import annotations

import asyncio
import uuid
import random
import logging
import time
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
    word_options_message,
    timer_message,
    leaderboard_message,
)
from .websocket import ConnectionManager

# logger
logging.basicConfig(
    filename="websocket.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)



class RoomManager:
    def __init__(self):
        self.rooms: dict[str, Game] = {}

    def create_room(self, settings: GameSettings) -> Game:
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

# Runtime tasks belong to networking, not GameEngine.
_turn_tasks: dict[str, asyncio.Task] = {}
_word_selection_tasks: dict[str, asyncio.Task] = {}
_phase_tasks: dict[str, asyncio.Task] = {}
_hint_tasks: dict[str, list[asyncio.Task]] = {}
_disconnect_tasks: dict[tuple[str, str], asyncio.Task] = {}
_chat_timestamps: dict[tuple[str, str], list[float]] = {}

# Player profile defaults
AVATAR_IDS = [
    "avatar_01",
    "avatar_02",
    "avatar_03",
    "avatar_04",
    "avatar_05",
    "avatar_06",
]

RANDOM_NAME_PARTS = [
    "Happy",
    "Lucky",
    "Swift",
    "Clever",
    "Tiny",
    "Mighty",
    "Sleepy",
    "Brave",
    "Pixel",
    "Sunny",
]

MAX_PLAYER_NAME_LENGTH = 18
CHAT_MAX_MESSAGES = 5
CHAT_WINDOW_SECONDS = 3

# ----------------------------
# Basic helpers
# ----------------------------


def generate_pid() -> str:
    return str(uuid.uuid4())

# Temporarly generate name and avatar for the user
def generate_random_name() -> str:
    return f"{random.choice(RANDOM_NAME_PARTS)}{random.randint(100, 999)}"


def generate_random_avatar() -> str:
    return random.choice(AVATAR_IDS)

def get_unique_player_name(game: Game, name: str) -> str:
    existing_names = {
        player.name
        for player in game.players.values()
    }

    if name not in existing_names:
        return name

    number = 2

    while f"{name}({number})" in existing_names:
        number += 1

    return f"{name}({number})"

def generate_room_id() -> str:
    return uuid.uuid4().hex[:6].upper()


def game_engine(game: Game) -> GameEngine:
    return GameEngine(game)


def current_drawer_pid(game: Game) -> str | None:
    turn = game.current_turn
    if turn is None:
        return None
    return getattr(turn, "drawer_pid", getattr(turn, "drawer_id", None))


def current_word(game: Game) -> str | None:
    if game.current_turn is None:
        return None
    return getattr(
        game.current_turn,
        "word",
        getattr(game.current_turn, "selected_word", None),
    )


def player_has_correct_guess(game: Game, pid: str) -> bool:
    guess = game.guesses.get(pid)
    return bool(guess and guess.correct)


def visible_word_for(game: Game, pid: str) -> str | None:
    """Return only the word that this specific client is allowed to see."""
    word = current_word(game)

    if word is None:
        return None

    if pid == current_drawer_pid(game):
        return word

    if player_has_correct_guess(game, pid):
        return word

    if game.state in {GameState.TURN_END, GameState.ROUND_END, GameState.GAME_END}:
        return word

    if game.state != GameState.PLAYING:
        return None

    return game_engine(game).get_word_pattern()



def is_chat_spam(room_id: str, pid: str) -> bool:
    now = time.monotonic()
    key = (room_id, pid)

    timestamps = _chat_timestamps.setdefault(key, [])

    timestamps[:] = [
        timestamp
        for timestamp in timestamps
        if now - timestamp < CHAT_WINDOW_SECONDS
    ]

    if len(timestamps) >= CHAT_MAX_MESSAGES:
        return True

    timestamps.append(now)
    return False



def serialize_player(player: Player) -> dict[str, Any]:
    return {
        "pid": player.pid,
        "name": player.name,
        "avatar": player.avatar,
        "room_id": player.room_id,
        "connected": player.connected,
    }


def serialize_players(game: Game) -> list[dict[str, Any]]:
    return [serialize_player(player) for player in game.players.values()]


def serialize_settings(settings: GameSettings) -> dict[str, Any]:
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


def serialize_game_state(game: Game, viewer_pid: str | None = None) -> dict[str, Any]:
    current_turn = game.current_turn
    return {
        "room_id": game.room_id,
        "state": game.state.value if hasattr(game.state, "value") else str(game.state),
        "players": serialize_players(game),
        "connected_players": list(game.connected_players),
        "settings": serialize_settings(game.settings),
        "host_pid": game.host_pid,
        "current_drawer": current_drawer_pid(game),
        "current_round": (
            game.current_round.round_number
            if game.current_round is not None
            else None
        ),
        "current_turn": (
            {
                "turn_id": current_turn.turn_id,
                "round_id": current_turn.round_id,
                "drawer_pid": current_drawer_pid(game),
            }
            if current_turn is not None
            else None
        ),
        "word": visible_word_for(game, viewer_pid) if viewer_pid else None,
        "word_available": (
            visible_word_for(game, viewer_pid) is not None
            if viewer_pid
            else False
        ),
    }


async def send_game_state(game: Game, pids: set[str] | list[str] | None = None):
    recipients = list(game.connected_players if pids is None else pids)
    for pid in recipients:
        await connection_manager.send_to_player(
            pid,
            ServerMessage(
                type="game_state",
                data=serialize_game_state(game, pid),
            ).to_dict(),
        )


async def send_error(pid: str, message: str):
    await connection_manager.send_to_player(pid, error_message(message))


def cancel_task(task_map: dict[Any, asyncio.Task], key: Any):
    task = task_map.pop(key, None)
    if task is not None and not task.done() and task is not asyncio.current_task():
        task.cancel()


def cancel_turn_runtime(game: Game):
    cancel_task(_turn_tasks, game.room_id)
    cancel_task(_word_selection_tasks, game.room_id)
    cancel_task(_phase_tasks, game.room_id)

    for task in _hint_tasks.pop(game.room_id, []):
        if not task.done():
            task.cancel()


def cancel_disconnect_grace(game: Game, pid: str):
    task = _disconnect_tasks.pop((game.room_id, pid), None)
    if task is not None and not task.done():
        task.cancel()


# ----------------------------
# Word / leaderboard messages
# ----------------------------


def word_option_payload(game: Game) -> list[dict[str, Any]]:
    result = []
    for option in game.current_word_options:
        result.append({
            "word_id": option[0],
            "word": option[1],
        })
    return result


def serialize_leaderboard(game: Game) -> list[dict[str, Any]]:
    rows = []
    for position, entry in enumerate(game_engine(game).get_leaderboard(), start=1):
        player = game.players.get(entry.pid)
        if player is None:
            continue
        rows.append({
            "position": position,
            "pid": entry.pid,
            "name": player.name,
            "avatar": player.avatar,
            "points": entry.points,
        })
    return rows


async def send_leaderboard(game: Game):
    await connection_manager.send_to_players(
        game.connected_players,
        leaderboard_message(serialize_leaderboard(game)),
    )


async def send_word_options(game: Game):
    drawer = current_drawer_pid(game)
    if drawer is None:
        return
    await connection_manager.send_to_player(
        drawer,
        word_options_message(word_option_payload(game)),
    )


async def broadcast_selected_word(game: Game):
    """Drawer gets the word; guessers get the current hidden pattern."""
    word = current_word(game)
    if word is None:
        return

    drawer = current_drawer_pid(game)
    pattern = game_engine(game).get_word_pattern()

    for pid in list(game.connected_players):
        payload = {
            "event": "word_selected",
            "word": word if pid == drawer else pattern,
            "pattern": pattern,
            "is_drawer": pid == drawer,
        }
        await connection_manager.send_to_player(
            pid,
            ServerMessage(type="game_state", data=payload).to_dict(),
        )


async def broadcast_word_visibility(game: Game):
    """Refresh word visibility after a correct guess or a hint."""
    word = current_word(game)
    if word is None:
        return

    pattern = game_engine(game).get_word_pattern()
    drawer = current_drawer_pid(game)

    for pid in list(game.connected_players):
        visible = (
            word
            if pid == drawer or player_has_correct_guess(game, pid)
            else pattern
        )
        await connection_manager.send_to_player(
            pid,
            ServerMessage(
                type="game_state",
                data={
                    "event": "word_visibility",
                    "word": visible,
                    "pattern": pattern,
                    "is_drawer": pid == drawer,
                    "correct": player_has_correct_guess(game, pid),
                },
            ).to_dict(),
        )


# ----------------------------
# Join / reconnect / lobby
# ----------------------------

async def handle_join(game: Game, pid: str, data: dict[str, Any]):
    # A known PID is always a reconnect, not a new player. The existing
    # profile is retained; the client does not need a profile-update message.
    if pid in game.players:
        await handle_reconnect(game, pid)
        return

    name = str(data.get("name", "")).strip()
    avatar = str(data.get("avatar", "")).strip()

    if len(name) > MAX_PLAYER_NAME_LENGTH:
        await send_error(
            pid,
            f"Player name cannot exceed {MAX_PLAYER_NAME_LENGTH} characters."
        )
        return

    if not name:
        name = generate_random_name()

    if not avatar:
        avatar = generate_random_avatar()
    elif avatar not in AVATAR_IDS:
        await send_error(pid, "Invalid avatar.")
        return

    name = get_unique_player_name(game, name)

    if game.state == GameState.GAME_END:
        await send_error(pid, "This game has already ended.")
        return

    max_players = max(1, int(game.settings.player_count))
    if len(game.players) >= max_players:
        await send_error(pid, "Room is full.")
        return

    player = Player(
        pid=pid,
        name=name,
        avatar=str(avatar),
        room_id=game.room_id,
        connected=True,
    )
    game.players[pid] = player

    if game.host_pid is None:
        game.host_pid = pid

    # Lobby join versus late join.
    if game.state == GameState.LOBBY:
        game.connected_players.add(pid)
    else:
        try:
            game_engine(game).add_late_player(pid)
        except Exception as exc:
            game.players.pop(pid, None)
            await send_error(pid, str(exc))
            return

    cancel_disconnect_grace(game, pid)

    await connection_manager.send_to_player(pid, player_joined(serialize_player(player)))
    await send_game_state(game, {pid})

    await connection_manager.send_to_players(
        game.connected_players - {pid},
        player_joined(serialize_player(player)),
    )
    await send_game_state(game, game.connected_players - {pid})

    if game.state != GameState.LOBBY:
        await broadcast_word_visibility(game)


async def handle_reconnect(game: Game, pid: str):
    player = game.players.get(pid)
    if player is None:
        await send_error(pid, "Player does not exist in this room.")
        return

    cancel_disconnect_grace(game, pid)
    player.connected = True
    player.room_id = game.room_id
    game.connected_players.add(pid)

    await send_game_state(game, {pid})

    if game.state == GameState.WORD_SELECTION and pid == current_drawer_pid(game):
        await send_word_options(game)
    elif game.state == GameState.PLAYING:
        await connection_manager.send_to_player(
            pid,
            ServerMessage(
                type="game_state",
                data={
                    "event": "word_visibility",
                    "word": visible_word_for(game, pid),
                    "pattern": game_engine(game).get_word_pattern(),
                    "is_drawer": pid == current_drawer_pid(game),
                    "correct": player_has_correct_guess(game, pid),
                },
            ).to_dict(),
        )

    await connection_manager.send_to_players(
        game.connected_players - {pid},
        system_message(f"{player.name} reconnected."),
    )
    await send_game_state(game, game.connected_players - {pid})


async def handle_lobby_update(game: Game, pid: str, data: dict[str, Any]):
    if game.state != GameState.LOBBY:
        await send_error(
            pid,
            "Lobby settings can only be changed before the game starts.",
        )
        return

    if pid != game.host_pid:
        await send_error(pid, "Only the host can update lobby settings.")
        return

    allowed = {
        "player_count",
        "language",
        "draw_time",
        "rounds",
        "word_count",
        "hints",
        "custom_words",
        "custom_words_only",
    }

    updates: dict[str, Any] = {}

    for field_name in allowed:
        if field_name not in data:
            continue

        value = data[field_name]

        if field_name in {
            "player_count",
            "draw_time",
            "rounds",
            "word_count",
            "hints",
        }:
            try:
                value = int(value)
            except (TypeError, ValueError):
                await send_error(pid, f"Invalid value for {field_name}.")
                return

        if field_name == "player_count" and value < 2:
            await send_error(pid, "player_count must be at least 2.")
            return

        if field_name == "draw_time" and value <= 0:
            await send_error(pid, "draw_time must be greater than 0.")
            return

        if field_name in {"rounds", "word_count"} and value <= 0:
            await send_error(pid, f"{field_name} must be greater than 0.")
            return

        if field_name == "hints" and value < 0:
            await send_error(pid, "hints cannot be negative.")
            return

        if field_name == "language":
            aliases = {
                "english": "en",
                "en": "en",
            }
            value = aliases.get(str(value).strip().lower(), value)

        updates[field_name] = value

    new_player_count = int(
        updates.get("player_count", game.settings.player_count)
    )

    # Capacity is based on all persistent players, including players in
    # the reconnect grace period.
    if len(game.players) > new_player_count:
        await send_error(
            pid,
            "New player limit cannot be lower than the current player count.",
        )
        return

    for field_name, value in updates.items():
        setattr(game.settings, field_name, value)

    await send_game_state(game)


# ----------------------------
# Chat / guessing
# ----------------------------

async def recipients_for_chat(game: Game, sender_pid: str) -> set[str]:
    if sender_pid == current_drawer_pid(game):
        return set(game.connected_players)

    if player_has_correct_guess(game, sender_pid):
        allowed = {current_drawer_pid(game), sender_pid}
        allowed |= {
            other_pid
            for other_pid in game.connected_players
            if player_has_correct_guess(game, other_pid)
        }
        return {pid for pid in allowed if pid is not None}

    return {
        pid for pid in game.connected_players
        if not player_has_correct_guess(game, pid)
        or pid == current_drawer_pid(game)
    }


async def handle_chat(game: Game, pid: str, data: dict[str, Any]):
    player = game.players.get(pid)
    if player is None or pid not in game.connected_players:
        await send_error(pid, "Player not found or disconnected.")
        return

    message = str(data.get("message", "")).strip()
    if not message:
        return

    if is_chat_spam(game.room_id, pid):
        await send_error(pid, "You are sending messages too quickly.")
        return

    if game.state != GameState.PLAYING or game.current_turn is None:
        recipients = await recipients_for_chat(game, pid)
        await connection_manager.send_to_players(
            recipients,
            chat_message(pid, player.name, message),
        )
        return

    result = game_engine(game).process_guess(pid, message)

    if result == "CHAT":
        recipients = await recipients_for_chat(game, pid)
        await connection_manager.send_to_players(
            recipients,
            chat_message(pid, player.name, message),
        )

    elif result == "CORRECT":
        await handle_correct_guess(game, pid, player.name)

    elif result == "CLOSE":
        recipients = await recipients_for_chat(game, pid)
        await connection_manager.send_to_players(
            recipients,
            chat_message(pid, player.name, message),
        )
        await connection_manager.send_to_player(
            pid,
            system_message("Your guess is close!"),
        )

    elif result == "WRONG":
        recipients = await recipients_for_chat(game, pid)
        await connection_manager.send_to_players(
            recipients,
            chat_message(pid, player.name, message),
        )

    elif isinstance(result, dict):
        await handle_correct_guess(
            game,
            pid,
            player.name,
            turn_end_result=result,
        )

    else:
        await send_error(pid, "Invalid guess result.")


async def handle_correct_guess(
    game: Game,
    pid: str,
    player_name: str,
    turn_end_result: dict[str, Any] | None = None,
):
    await connection_manager.send_to_player(pid, system_message("Correct guess!"))
    await connection_manager.send_to_players(
        game.connected_players - {pid},
        system_message(f"{player_name} guessed correctly!"),
    )

    if turn_end_result is None and game_engine(game).all_guessers_correct():
        turn_end_result = game_engine(game).end_turn("ALL_GUESSERS_CORRECT")

    if turn_end_result is not None:
        await finish_turn(game, turn_end_result)
        return

    await broadcast_word_visibility(game)
    await send_game_state(game)


# ----------------------------
# Word selection + timers
# ----------------------------

async def handle_select_word(game: Game, pid: str, data: dict[str, Any]):
    if game.state != GameState.WORD_SELECTION:
        await send_error(pid, "The game is not waiting for word selection.")
        return

    if pid != current_drawer_pid(game):
        await send_error(pid, "Only the drawer can select a word.")
        return

    word_id = data.get("word_id")
    if word_id is None:
        await send_error(pid, "word_id is required.")
        return

    try:
        game_engine(game).select_word(int(word_id))
    except Exception as exc:
        await send_error(pid, str(exc))
        return

    cancel_task(_word_selection_tasks, game.room_id)
    await broadcast_selected_word(game)
    await send_game_state(game)
    await start_playing_runtime(game)


async def start_playing_runtime(game: Game):
    cancel_task(_turn_tasks, game.room_id)

    for task in _hint_tasks.pop(game.room_id, []):
        if not task.done() and task is not asyncio.current_task():
            task.cancel()

    turn = game.current_turn
    if turn is None:
        return

    draw_task = asyncio.create_task(
        turn_timeout_worker(game, turn.turn_id)
    )
    _turn_tasks[game.room_id] = draw_task

    hints = max(0, int(game.settings.hints))
    if hints <= 0:
        return

    max_hints = min(
        hints,
        game_engine(game).get_max_hints(sum(turn.word_lengths or [])),
    )
    if max_hints <= 0:
        return

    # Hints are evenly distributed through the drawing period.
    # Example: 2 hints in an 80-second turn -> at 26s and 53s.
    interval = max(1.0, game.settings.draw_time / (max_hints + 1))
    tasks = [
        asyncio.create_task(
            hint_worker(game, turn.turn_id, interval * (index + 1))
        )
        for index in range(max_hints)
    ]
    _hint_tasks[game.room_id] = tasks


async def hint_worker(game: Game, turn_id: str, delay: float):
    try:
        await asyncio.sleep(delay)

        if (
            game.current_turn is None
            or game.current_turn.turn_id != turn_id
            or game.state != GameState.PLAYING
        ):
            return

        pattern = game_engine(game).reveal_hint()
        if pattern is not None:
            await broadcast_word_visibility(game)
            await send_game_state(game)
    except asyncio.CancelledError:
        return


async def turn_timeout_worker(game: Game, turn_id: str):
    try:
        total = max(1, int(game.settings.draw_time))

        for remaining in range(total, 0, -1):
            if (
                game.current_turn is None
                or game.current_turn.turn_id != turn_id
                or game.state != GameState.PLAYING
            ):
                return

            await connection_manager.send_to_players(
                game.connected_players,
                timer_message(remaining, "drawing"),
            )
            await asyncio.sleep(1)

        if (
            game.current_turn is None
            or game.current_turn.turn_id != turn_id
            or game.state != GameState.PLAYING
        ):
            return

        result = game_engine(game).end_turn("TIME_UP")
        await finish_turn(game, result)
    except asyncio.CancelledError:
        return


async def finish_turn(game: Game, turn_end_result: dict[str, Any]):
    cancel_turn_runtime(game)

    # TURN_END state makes visible_word_for() reveal the complete answer.
    await send_game_state(game)

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

    await send_leaderboard(game)

    # The leaderboard is intentionally visible for 7 seconds.
    _phase_tasks[game.room_id] = asyncio.create_task(
        advance_after_turn(game)
    )


async def advance_after_turn(game: Game):
    try:
        for remaining in range(7, 0, -1):
            if game.state != GameState.TURN_END:
                return

            await connection_manager.send_to_players(
                game.connected_players,
                timer_message(remaining, "leaderboard"),
            )
            await asyncio.sleep(1)

        if game.state != GameState.TURN_END:
            return

        engine = game_engine(game)
        engine.next_turn()

        if game.state == GameState.TURN_START:
            await send_game_state(game)
            await start_turn_runtime(game)

        elif game.state == GameState.ROUND_END:
            await send_game_state(game)

            # A short 3-second round transition precedes the next round.
            for remaining in range(3, 0, -1):
                if game.state != GameState.ROUND_END:
                    return
                await connection_manager.send_to_players(
                    game.connected_players,
                    timer_message(remaining, "round_start"),
                )
                await asyncio.sleep(1)

            engine.next_round()

            if game.state == GameState.ROUND_START:
                await send_game_state(game)
                await start_round_runtime(game)
            else:
                await send_leaderboard(game)
                await send_game_state(game)

                for remaining in range(7, 0, -1):
                    if game.state != GameState.GAME_END:
                        return

                    await connection_manager.send_to_players(
                        game.connected_players,
                        timer_message(remaining, "leaderboard"),
                    )

                    await asyncio.sleep(1)

                # Return the existing room to the lobby
                engine.reset_to_lobby()
                await send_game_state(game)

    except asyncio.CancelledError:
        return


async def start_round_runtime(game: Game):
    cancel_task(_phase_tasks, game.room_id)

    engine = game_engine(game)
    engine.start_round()
    await send_game_state(game)

    for remaining in range(3, 0, -1):
        if game.state != GameState.TURN_START:
            return

        await connection_manager.send_to_players(
            game.connected_players,
            timer_message(remaining, "round_start"),
        )
        await asyncio.sleep(1)

    if game.state == GameState.TURN_START:
        await start_turn_runtime(game)


async def start_turn_runtime(game: Game):
    engine = game_engine(game)

    if game.state != GameState.TURN_START:
        return

    if not game.connected_players:
        engine.next_round()
        await send_game_state(game)
        return

    engine.start_turn()
    await send_game_state(game)

    options = engine.word_selection()
    if not options:
        result = engine.end_turn("NO_WORD_OPTIONS")
        await finish_turn(game, result)
        return

    await send_word_options(game)

    # Drawer has exactly 15 seconds to choose a word.
    selection_task = asyncio.create_task(
        word_selection_timeout_worker(
            game,
            game.current_turn.turn_id,
        )
    )
    _word_selection_tasks[game.room_id] = selection_task


async def word_selection_timeout_worker(game: Game, turn_id: str):
    try:
        for remaining in range(15, 0, -1):
            if (
                game.current_turn is None
                or game.current_turn.turn_id != turn_id
                or game.state != GameState.WORD_SELECTION
            ):
                return

            await connection_manager.send_to_players(
                game.connected_players,
                timer_message(remaining, "word_selection"),
            )
            await asyncio.sleep(1)

        if (
            game.current_turn is None
            or game.current_turn.turn_id != turn_id
            or game.state != GameState.WORD_SELECTION
        ):
            return

        if not game.current_word_options:
            result = game_engine(game).end_turn("NO_WORD_OPTIONS")
            await finish_turn(game, result)
            return

        # If the drawer does not choose, automatically select the first option.
        word_id = game.current_word_options[0][0]
        game_engine(game).select_word(word_id)

        await broadcast_selected_word(game)
        await send_game_state(game)
        await start_playing_runtime(game)

    except asyncio.CancelledError:
        return


async def handle_start_game(game: Game, pid: str):
    if pid != game.host_pid:
        await send_error(pid, "Only the host can start the game.")
        return

    if game.state != GameState.LOBBY:
        await send_error(pid, "The game has already started.")
        return

    if len(game.connected_players) < 2:
        await send_error(pid, "Not enough players to start the game.")
        return

    try:
        game_engine(game).start_game()
    except Exception as exc:
        await send_error(pid, str(exc))
        return

    await send_game_state(game)
    await start_round_runtime(game)


# ----------------------------
# Drawing
# ----------------------------

async def handle_draw(game: Game, pid: str, data: dict[str, Any]):
    if game.state != GameState.PLAYING:
        await send_error(pid, "Drawing is not active.")
        return

    if pid != current_drawer_pid(game):
        await send_error(pid, "Only the drawer can draw.")
        return

    await connection_manager.send_to_players(
        game.connected_players - {pid},
        ServerMessage(
            type="draw",
            data={"pid": pid, **data},
        ).to_dict(),
    )


# ----------------------------
# Disconnect / grace period
# ----------------------------

async def permanent_remove_player(game: Game, pid: str):
    task_key = (game.room_id, pid)
    _disconnect_tasks.pop(task_key, None)

    player = game.players.get(pid)

    if player is None or player.connected:
        return

    was_host = game.host_pid == pid

    engine = game_engine(game)

    # Check whether this player is the current drawer BEFORE
    # permanently removing their scoring/player data.
    is_current_drawer = (
        game.current_turn is not None
        and current_drawer_pid(game) == pid
        and game.state in {
            GameState.WORD_SELECTION,
            GameState.PLAYING
        }
    )

    # If the disconnected player was the drawer, end their turn first.
    # This gives the drawer 0 artist points and creates the normal
    # TURN_END result before their player data is removed.
    if is_current_drawer:
        turn_end_result = engine.end_turn("DRAWER_DISCONNECTED")

        await connection_manager.send_to_players(
            game.connected_players,
            system_message(
                f"{player.name} did not reconnect. "
                "The turn has ended."
            ),
        )

        # Permanently remove the player after the turn result
        # has been calculated.
        engine.remove_player(pid)

        # Show the normal turn-end screen/leaderboard.
        await finish_turn(game, turn_end_result)

    else:
        # Normal permanent removal for a non-drawer.
        engine.remove_player(pid)

    # If the host reaches permanent removal while the room
    # still exists, assign an active player as the new host.
    if was_host and game.connected_players:
        game.host_pid = next(iter(game.connected_players))

        await connection_manager.send_to_players(
            game.connected_players,
            system_message(
                f"Host left. {game.players[game.host_pid].name} is now the host."
            ),
        )

    await connection_manager.send_to_players(
        game.connected_players,
        player_left(pid),
    )

    await send_game_state(game)

async def disconnect_grace_worker(game: Game, pid: str, seconds: int = 15):
    try:
        await asyncio.sleep(seconds)
        await permanent_remove_player(game, pid)
    except asyncio.CancelledError:
        return


async def handle_disconnect(game: Game, pid: str):
    player = game.players.get(pid)
    if player is None:
        return

    game.connected_players.discard(pid)
    player.connected = False

    # If nobody is active anymore, delete the room immediately.
    if not game.connected_players:
        cancel_turn_runtime(game)
        room_manager.remove_room(game.room_id)
        return

    # Host keeps their role during the 15-second reconnect grace period.
    if game.host_pid == pid:
        await connection_manager.send_to_players(
            game.connected_players,
            system_message(
                f"{player.name} lost connection. "
                "They can reconnect within 15 seconds."
            ),
        )
    else:
        await connection_manager.send_to_players(
            game.connected_players,
            system_message(
                f"{player.name} disconnected. "
                "They can reconnect for 15 seconds."
            ),
        )

    # GameEngine decides immediate gameplay consequences; networking only
    # manages the connection and the later grace-period removal.
    result = game_engine(game).handle_disconnect(pid)

    if result == "GAME_END":
        await connection_manager.send_to_players(
            game.connected_players,
            system_message("Game ended because too few players remain."),
        )
        cancel_turn_runtime(game)
    elif result == "DRAWER_DISCONNECTED":
        await connection_manager.send_to_players(
            game.connected_players,
            system_message("The drawer disconnected. The turn has ended."),
        )
        await finish_turn(game, {
            "word": current_word(game),
            "reason": "DRAWER_DISCONNECTED",
            "points_awarded": game.current_turn.points_awarded if game.current_turn else {},
        })
    elif result == "GUESSER_DISCONNECTED":
        await connection_manager.send_to_players(
            game.connected_players,
            system_message("All remaining guessers are correct."),
        )

    await send_game_state(game)

    cancel_disconnect_grace(game, pid)
    task = asyncio.create_task(disconnect_grace_worker(game, pid))
    _disconnect_tasks[(game.room_id, pid)] = task


# ----------------------------
# Message routing / websocket
# ----------------------------

async def handle_message(game: Game, pid: str, message: dict[str, Any]):
    client_message = ClientMessage.from_dict(message)
    message_type = client_message.type
    data = client_message.data

    if message_type == "join":
        await handle_join(game, pid, data)
    elif message_type == "chat":
        await handle_chat(game, pid, data)
    elif message_type == "select_word":
        await handle_select_word(game, pid, data)
    elif message_type == "draw":
        await handle_draw(game, pid, data)
    elif message_type == "lobby_update":
        await handle_lobby_update(game, pid, data)
    elif message_type == "start_game":
        await handle_start_game(game, pid)
    elif message_type == "reconnect":
        await handle_reconnect(game, pid)
    else:
        await send_error(pid, f"Unknown message type: {message_type}")


async def websocket_endpoint(websocket: WebSocket, room_id: str):
    pid = websocket.query_params.get("pid") or generate_pid()
    game = room_manager.get_room(room_id)

    if game is None:
        await websocket.accept()
        await websocket.send_json(error_message("Room not found."))
        await websocket.close()
        return

    await connection_manager.connect(pid, websocket)

    try:
        await websocket.send_json(
            ServerMessage(
                type="connection",
                data={"pid": pid, "room_id": room_id},
            ).to_dict()
        )

        while True:
            message = await websocket.receive_json()

            logger.info(
                "RECEIVED | room=%s | pid=%s | %s",
                room_id,
                pid,
                message
            )

            await handle_message(game, pid, message)

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await send_error(pid, f"Server error: {exc}")
        except Exception:
            pass
    finally:
        connection_manager.disconnect(pid)
        await handle_disconnect(game, pid)
