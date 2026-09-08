from dataclasses import dataclass
from datetime import datetime

@dataclass
class Turn:
    turn_id: str
    round_id: str
    drawer_pid: str
    word_id: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None