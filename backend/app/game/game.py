from dataclasses import dataclass, field

from .state import GameState
from ..models.player import Player
from ..models.gamesettings import GameSettings
from ..models.round import Round
from ..models.turn import Turn
from ..models.guess import Guess
from ..models.leaderboard import Leaderboard
from ..models.chatmessage import ChatMessage

@dataclass
class Game:
    # Fields without defaults must come before fields with defaults.
    room_id: str
    state: GameState
    settings: GameSettings 

    chat_history: list[ChatMessage] = field(default_factory=list)
    players: dict[str, Player] = field(default_factory=dict)
    connected_players: set[str] = field(default_factory=set)
    
    turn_order: list[str] = field(default_factory=list)
    current_turn_index: int = 0

    word_pool: list = field(default_factory=list)
    current_word_options: list = field(default_factory=list)

    current_round: Round | None = None
    current_turn: Turn | None = None
    guesses: dict[str, Guess] = field(default_factory=dict)
    leaderboard: dict[str, Leaderboard] = field(default_factory=dict)