from dataclasses import dataclass

@dataclass
class Player:
    pid: str
    name: str
    avatar: str
    room_id: str | None = None
    connected: bool = False