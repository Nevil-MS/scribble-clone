from dataclasses import dataclass

@dataclass
class GameSettings:
    room_id: str
    player_count: int
    language: str
    draw_time: str
    draw_time: int
    rounds: int
    word_count: int
    hints: int
    custom_words: list[str]
    custom_words_only: bool