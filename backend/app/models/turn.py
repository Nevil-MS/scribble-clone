from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Turn:
    turn_id: str
    round_id: str
    drawer_pid: str
    word: str | None = None
    word_lengths: list[int] | None = None
    started_at: datetime | None = None
    points_awarded: dict[str, int] = field(default_factory=dict)