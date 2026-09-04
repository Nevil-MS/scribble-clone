from dataclasses import dataclass
from datetime import datetime

@dataclass
class Guess:
    guess_id: str
    turn_id: str
    pid: str
    correct: bool
    guessed_at: datetime
    points_awarded: int