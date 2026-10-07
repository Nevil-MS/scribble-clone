from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(
        self,
        pid: str,
        websocket: WebSocket,
    ):
        await websocket.accept()
        self.connections[pid] = websocket

    def disconnect(self, pid: str):
        self.connections.pop(pid, None)

    def get_connection(self, pid: str) -> WebSocket | None:
        return self.connections.get(pid)

    def is_connected(self, pid: str) -> bool:
        return pid in self.connections

    async def send_to_player(
        self,
        pid: str,
        message: dict,
    ):
        websocket = self.connections.get(pid)

        if websocket is None:
            return

        try:
            logger.info(
                "SENT | pid=%s | %s",
                pid,
                message
            )

            await websocket.send_json(message)
        except Exception:
            self.disconnect(pid)

    async def send_to_players(
        self,
        pids: set[str] | list[str],
        message: dict,
    ):
        for pid in list(pids):
            await self.send_to_player(pid, message)

    async def broadcast(
        self,
        message: dict,
    ):
        for pid in list(self.connections.keys()):
            await self.send_to_player(pid, message)

    async def broadcast_except(
        self,
        excluded_pid: str,
        message: dict,
    ):
        for pid in list(self.connections.keys()):
            if pid != excluded_pid:
                await self.send_to_player(pid, message)