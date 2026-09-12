from dataclasses import dataclass, field

from .state import GameState
from ..models.player import Player
from ..models.gamesettings import GameSettings
from ..models.round import Round
from ..models.turn import Turn
from ..models.guess import Guess
from ..models.leaderboard import Leaderboard

@dataclass
class Game:
    # Fields without defaults must come before fields with defaults.
    room_id: str
    state: GameState
    settings: GameSettings 

    players: dict[str, Player] = field(default_factory=dict)
    turn_order: list[str] = field(default_factory=list)
    current_turn_index: int = 0
    current_round: Round | None = None
    current_turn: Turn | None = None
    guesses: dict[str, Guess] = field(default_factory=dict)
    leaderboard: dict[str, Leaderboard] = field(default_factory=dict)