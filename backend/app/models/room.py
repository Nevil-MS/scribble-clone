from dataclasses import dataclass
from datetime import datetime

@dataclass
class Room:
    room_id: str
    host_pid: str
    status: str
    created_at: datetime