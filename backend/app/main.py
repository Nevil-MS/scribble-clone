from fastapi import FastAPI, WebSocket

from .networking.handlers import (
    room_manager,
    websocket_endpoint,
    generate_room_id,
    generate_pid,
    generate_random_name,
    generate_random_avatar,
)
from .models.gamesettings import GameSettings
from .models.player import Player

app = FastAPI(
    title="Skribbl Clone Backend",
)


@app.get("/")
async def root():
    return {
        "message": "Skribbl Clone backend is running"
    }


@app.post("/rooms")
async def create_room(
    name: str | None = None,
    avatar: str | None = None,
):
    room_id = generate_room_id()
    pid = generate_pid()

    if not name:
        name = generate_random_name()

    if not avatar:
        avatar = generate_random_avatar()

    settings = GameSettings(
        room_id=room_id,
        player_count=2,
        language="English",
        draw_time=60,
        rounds=3,
        word_count=3,
        hints=0,
        custom_words=[],
        custom_words_only=False,
    )

    room = room_manager.create_room(settings)

    player = Player(
        pid=pid,
        name=name,
        avatar=avatar,
        room_id=room_id,
        connected=False,
    )
    
    room.players[pid] = player
    room.host_pid = pid

    return {
        "room_id": room.room_id,
        "pid": pid,
        "name": player.name,
        "avatar": player.avatar,
        "message": "Room created successfully",
    }

@app.websocket("/ws/{room_id}")
async def websocket_route(
    websocket: WebSocket,
    room_id: str,
):
    await websocket_endpoint(
        websocket,
        room_id,
    )