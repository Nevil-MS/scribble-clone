from datetime import datetime
import random
import uuid
import json

from .game import Game
from .state import GameState
from ..models.round import Round
from ..models.turn import Turn
from ..models.guess import Guess
from ..database.word_repository import get_random_words
from ..models.chatmessage import ChatMessage
from ..models.leaderboard import Leaderboard


class GameEngine:

    def __init__(self, game: Game):
        # Handles game rules and state transitions for the given game.
        self.game = game



    def start_game(self):
        # Generate one turn order and reuse it across all rounds.
        turn_order = list(self.game.players.keys())
        random.shuffle(turn_order)

        self.game.turn_order = turn_order
        self.game.current_turn_index = 0

        # Reserve enough unique word options for every turn in the game.
        required_words = (
            self.game.settings.player_count
            * self.game.settings.rounds
            * self.game.settings.word_count
        )

        self.game.word_pool = get_random_words(
            required_words,
            self.game.settings.language
        )

        self.game.leaderboard = {
            pid: Leaderboard(pid=pid, points=0)
            for pid in self.game.players
        }

        if len(self.game.word_pool) < required_words:
            raise ValueError("Not enough words available for this game.")

        self.game.state = GameState.ROUND_START



    def handle_disconnect(self, pid: str):
        if len(self.game.connected_players) < 2:
            self.game.state = GameState.GAME_END
            return

        if (
            self.game.current_turn
            and pid == self.game.current_turn.drawer_pid
            and self.game.state in {
                GameState.WORD_SELECTION,
                GameState.PLAYING
            }
        ):
            return self.end_turn("DRAWER_DISCONNECTED")

        if (
            self.game.state == GameState.PLAYING
            and self.all_guessers_correct()
        ):
            return self.end_turn("GUESSER_DISCONNECTED")

        return "CONTINUE"


    def start_round(self):
        # Create the next round, starting from round 1 if this is a new game.
        if self.game.current_round is None:
            round_number = 1
        else:
            round_number = self.game.current_round.round_number + 1

        new_round = Round(
            round_id=str(uuid.uuid4()),
            room_id=self.game.room_id,
            round_number=round_number
        )

        self.game.current_round = new_round
        self.game.current_turn_index = 0
        self.game.state = GameState.TURN_START



    def start_turn(self):
        # The turn order determines who draws this turn.
        drawer_pid = self.game.turn_order[self.game.current_turn_index]

        new_turn = Turn(
            turn_id=str(uuid.uuid4()),
            round_id=self.game.current_round.round_id,
            drawer_pid=drawer_pid,
            points_awarded={
                pid: 0 for pid in self.game.players
            }
        )

        self.game.current_turn = new_turn

        # Guesses belong to a single turn, so previous turn's guesses
        # must not carry over.
        self.game.guesses = {}

        self.game.state = GameState.WORD_SELECTION



    def word_selection(self):
        word_count = self.game.settings.word_count

        # All presented options are consumed, including words not selected.
        options = self.game.word_pool[:word_count]
        self.game.word_pool = self.game.word_pool[word_count:]

        # Keep the options so the later selection can be validated.
        self.game.current_word_options = options

        return options



    def select_word(self, word_id: int):
        selected_word = None

        # Only words presented for this turn can be selected.
        for option in self.game.current_word_options:
            # Database row: (word_id, word, word_lengths, language)
            if option[0] == word_id:
                selected_word = option
                break

        if selected_word is None:
            raise ValueError("Invalid word selection.")

        self.game.current_turn.word = selected_word[1]
        self.game.current_turn.word_lengths = json.loads(selected_word[2])

        self.game.current_turn.started_at=datetime.now()

        self.game.state = GameState.PLAYING



    def is_close_guess(self, guess: str, answer:str):
        guess = guess.strip().lower()
        answer = answer.strip().lower()

        # Threshold = 2 if any part of word is longer than 5 letter
        # else 1
        threshold = 2 if any(
            length > 5
            for length in self.game.current_turn.word_lengths
        ) else 1


        # Levenshtein Distance Algorithm
        previous_row = list(range(len(answer) + 1))

        for i, guess_char in enumerate(guess, start=1):
            current_row = [i]

            for j, answer_char in enumerate(answer, start=1):
                insert_cost = current_row[j - 1] + 1
                delete_cost = previous_row[j] + 1
                replace_cost = previous_row[j - 1] + (guess_char != answer_char)

                current_row.append(
                    min(insert_cost, delete_cost, replace_cost)
                )

            previous_row = current_row

        return previous_row[-1] <= threshold



    def all_guessers_correct(self): 
        guessers = ( 
            self.game.connected_players 
            - {self.game.current_turn.drawer_pid} 
        ) 
    
        return all( 
            pid in self.game.guesses 
            for pid in guessers 
        )



    def process_guess(self, pid: str, message: str):

        if pid == self.game.current_turn.drawer_pid:
            return "CHAT"

        if pid in self.game.guesses and self.game.guesses[pid].correct:
            return "CHAT"

        answer = self.game.current_turn.word

        if message.strip().lower() == answer.lower():

            # how many seconds passed since turn start
            elapsed_time = (
                datetime.now() - self.game.current_turn.started_at
            ).total_seconds()

            # how many second left from draw time
            remaining_time = max(
                0,
                self.game.settings.draw_time - int(elapsed_time)
            )

            speed_bonus = 150 * (
                remaining_time / self.game.settings.draw_time
            )

            # Guesser points = 150 base points + up to 150 speed bonus.
            # Speed bonus = 150 × (remaining time / total draw time).
            points = int(150 + speed_bonus)

            guess = Guess(
                guess_id = str(uuid.uuid4()),
                turn_id = self.game.current_turn.turn_id,
                pid = pid,
                correct = True,
                guessed_at = datetime.now(),
                points_awarded = points
            )

            self.game.guesses[pid] = guess
            self.add_points(pid, points)

            if self.all_guessers_correct():
                return self.end_turn("WORD_GUESSED")

            return "CORRECT"

        if self.is_close_guess(message, answer):
            return "CLOSE"

        return "WRONG"



    def add_chat_message(self, pid: str, message: str):
        chat_message = ChatMessage(
            pid=pid,
            message=message,
            sent_at=datetime.now()
        )

        self.game.chat_history.append(chat_message)

        return chat_message



    def add_points(self, pid: str, points: int):
        self.game.leaderboard[pid].points += points
        self.game.current_turn.points_awarded[pid] += points



    def calculate_artist_points(self):
        # Calculate artist points from the successful guesses in this turn.

        draw_time = self.game.settings.draw_time
        eligible_guessers = self.game.settings.player_count - 1

        speed_total = 0

        for guess in self.game.guesses.values():
            elapsed_time = (
                guess.guessed_at - self.game.current_turn.started_at
            ).total_seconds()

            remaining_time = max(
                0,
                draw_time - int(elapsed_time)
            )

            speed_factor = remaining_time / draw_time
            speed_total += speed_factor

        # Artist points = 450 × average speed factor of all correct guessers.
        # Speed factor = remaining time / total draw time.
        artist_points = 450 * (
        speed_total / eligible_guessers
        )

        return min(450, int(artist_points))

    

    def end_turn(self, reason: str):
        artist_points = self.calculate_artist_points()

        drawer_pid = self.game.current_turn.drawer_pid
        self.add_points(drawer_pid, artist_points)

        self.game.state = GameState.TURN_END

        return {
            "word": self.game.current_turn.word,
            "reason": reason,
            "points_awarded": self.game.current_turn.points_awarded
        }



    def next_turn(self):
        while self.game.current_turn_index + 1 < len(self.game.turn_order):
            self.game.current_turn_index += 1

            next_pid = self.game.turn_order[
                self.game.current_turn_index
            ]

            if next_pid in self.game.connected_players:
                self.game.state = GameState.TURN_START
                return

        self.game.state = GameState.ROUND_END

    

    def next_round(self):
        if self.game.current_round.round_number < self.game.settings.rounds:
            self.game.state = GameState.ROUND_START

        else:
            self.game.state = GameState.GAME_END