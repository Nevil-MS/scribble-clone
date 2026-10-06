import asyncio
import json
import websockets


async def test():
    room_id = "CD7A6E"

    uri = f"ws://127.0.0.1:8000/ws/{room_id}"

    async with websockets.connect(uri) as websocket:
        print("Connected!")

        message = await websocket.recv()
        print("Server:", json.loads(message))

        await websocket.send(json.dumps({
            "type": "join",
            "data": {
                "name": "Neha",
                "avatar": "avatar-1"
            }
        }))

        for _ in range(2):
            message = await websocket.recv()
            print("Server:", json.loads(message))


asyncio.run(test())