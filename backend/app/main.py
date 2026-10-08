from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import os
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


app = FastAPI(title="Skribbl Clone Backend")

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],   
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
        player_count=3,
        language="en",
        draw_time=80,
        rounds=3,
        word_count=3,
        hints=2,
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