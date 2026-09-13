import random
import uuid

from .game import Game
from .state import GameState
from ..models.round import Round
from ..models.turn import Turn

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
            round_number = self.game.current_round.round_number + 1

        new_round = Round(
            round_id = str(uuid.uuid4()),
            room_id = self.game.room_id,
            round_number = round_number
        )
        
        self.game.current_round = new_round
        self.game.current_turn_index = 0
        self.game.state = GameState.TURN_START

    def start_turn(self):
        drawer_pid = self.game.turn_order[self.game.current_turn_index]

        new_turn = Turn(
            turn_id = str(uuid.uuid4()),
            round_id = self.game.current_round.round_id,
            drawer_pid = drawer_pid
        )

        self.game.current_turn = new_turn
        self.game.state = GameState.WORD_SELECTION

    def word_selection(self):
                

