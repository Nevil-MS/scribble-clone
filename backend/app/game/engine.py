import random
import uuid

from .game import Game
from .state import GameState

class GameEngine:
    def __init__(self, game: Game):
        self.game = game

    def start_game(self):
        turn_order = list(self.game.players.keys())
        random.shuffle(turn_order)

        self.game.turn_order = turn_order
        self.game.current_turn_index = 0
        self.game.state = GameState.ROUND_START

    def start_round(self):
        if self.game.current_round is None:
            round_number = 1
        else:
            round_number
