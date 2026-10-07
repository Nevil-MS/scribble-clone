import asyncio
import json
import uuid

import websockets


class TestPlayer:
    def __init__(self, name: str, pid: str | None = None):
        self.name = name
        self.pid = pid or str(uuid.uuid4())

        self.ws = None

        # Every received message is preserved.
        self.messages = []
        self.message_event = asyncio.Event()

        self._receiver_task = None

    async def connect(self, base_url: str, room_id: str):
        url = f"{base_url}/ws/{room_id}?pid={self.pid}"

        print(f"{self.name} connecting to {url}")

        self.ws = await websockets.connect(url)

        # The first message is always the connection message.
        raw = await self.ws.recv()
        message = json.loads(raw)

        print(f"{self.name} initial message: {message}")

        assert message["type"] == "connection", (
            f"{self.name} expected connection message, got: {message}"
        )

        assert message["data"]["pid"] == self.pid
        assert message["data"]["room_id"] == room_id

        self._receiver_task = asyncio.create_task(
            self._receiver()
        )

    async def _receiver(self):
        try:
            async for raw in self.ws:
                message = json.loads(raw)

                self.messages.append(message)
                self.message_event.set()

        except Exception:
            pass

    async def send(
        self,
        message_type: str,
        data: dict | None = None,
    ):
        assert self.ws is not None, "WebSocket is not connected."

        message = {
            "type": message_type,
            "data": data or {},
        }

        await self.ws.send(json.dumps(message))

    async def join(self):
        await self.send(
            "join",
            {
                "name": self.name,
                "avatar": "avatar_01",
            },
        )

    async def chat(self, message: str):
        await self.send(
            "chat",
            {
                "message": message,
            },
        )

    async def draw(self, **data):
        await self.send("draw", data)

    async def select_word(self, word_id: int):
        await self.send(
            "select_word",
            {
                "word_id": word_id,
            },
        )

    async def lobby_update(self, **settings):
        await self.send(
            "lobby_update",
            settings,
        )

    async def start_game(self):
        await self.send("start_game")

    async def reconnect(self):
        await self.send("reconnect")

    async def wait_for(
        self,
        message_type: str,
        timeout: float = 10,
        predicate=None,
    ):
        async def _wait():
            while True:

                # Search everything received so far.
                for message in self.messages:
                    if message.get("type") != message_type:
                        continue

                    if predicate is not None and not predicate(message):
                        continue

                    # Consume only the message we matched.
                    self.messages.remove(message)

                    return message

                self.message_event.clear()

                try:
                    await self.message_event.wait()
                except asyncio.CancelledError:
                    raise

        return await asyncio.wait_for(
            _wait(),
            timeout=timeout,
        )

    def clear_messages(self, message_type: str | None = None):
        if message_type is None:
            self.messages.clear()
        else:
            self.messages = [m for m in self.messages if m.get("type") != message_type]

    async def wait_for_state(
        self,
        state: str,
        timeout: float = 10,
        predicate=None,
    ):
        def matches(message):
            if message.get("data", {}).get("state") != state:
                return False
            if predicate is not None:
                return predicate(message)
            return True

        return await self.wait_for(
            "game_state",
            timeout=timeout,
            predicate=matches,
        )

    async def wait_for_event(
        self,
        event: str,
        timeout: float = 10,
        predicate=None,
    ):
        def matches(message):
            if message.get("data", {}).get("event") != event:
                return False
            if predicate is not None:
                return predicate(message)
            return True

        return await self.wait_for(
            "game_state",
            timeout=timeout,
            predicate=matches,
        )

    async def wait_for_timer(
        self,
        phase: str,
        timeout: float = 10,
        predicate=None,
    ):
        def matches(message):
            if message.get("data", {}).get("phase") != phase:
                return False

            if predicate is not None:
                return predicate(message)

            return True

        return await self.wait_for(
            "timer",
            timeout=timeout,
            predicate=matches,
        )

    async def expect_no_message(
        self,
        message_type: str,
        timeout: float = 1,
        predicate=None,
    ):
        try:
            await self.wait_for(
                message_type,
                timeout=timeout,
                predicate=predicate,
            )
        except asyncio.TimeoutError:
            return

        raise AssertionError(
            f"{self.name} unexpectedly received "
            f"{message_type}"
        )

    async def close(self):
        if self._receiver_task is not None:
            self._receiver_task.cancel()

        if self.ws is not None:
            try:
                await self.ws.close()
            except Exception:
                pass