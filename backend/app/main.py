from fastapi import FastAPI, WebSocket

from .networking.handlers import (
    room_manager,
    websocket_endpoint,
    generate_room_id,
)
from .models.gamesettings import GameSettings


app = FastAPI(
    title="Skribbl Clone Backend",
)


@app.get("/")
async def root():
    return {
        "message": "Skribbl Clone backend is running"
    }


@app.post("/rooms")
async def create_room():
    room_id = generate_room_id()

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

    return {
        "room_id": room.room_id,
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