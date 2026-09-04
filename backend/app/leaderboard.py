from dataclasses import dataclass

@dataclass
class Leaderboard:
    room_id: str
    pid: str
    points: int