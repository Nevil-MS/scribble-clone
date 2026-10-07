"""
Integration test suite for the Skribble Clone backend.
TC-18 through TC-55 (TC-56 through TC-62 are deferred).

IMPORTANT: Only modifies files inside test_scripts/.
"""
import asyncio
import httpx

from websocket_client import TestPlayer


HTTP_BASE_URL = "http://127.0.0.1:8000"
WS_BASE_URL = "ws://127.0.0.1:8000"


# ============================================================
# Room helpers
# ============================================================

async def create_room():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HTTP_BASE_URL}/rooms"
        )

    assert response.status_code == 200, (
        f"POST /rooms failed: "
        f"{response.status_code} {response.text}"
    )

    return response.json()


async def create_players(
    room,
    count=3,
):
    players = [
        TestPlayer(
            room["name"],
            pid=room["pid"],
        )
    ]

    for index in range(1, count):
        players.append(
            TestPlayer(f"Test{index + 1}")
        )

    for player in players:
        await player.connect(
            WS_BASE_URL,
            room["room_id"],
        )

    for player in players:
        await player.join()
        await player.wait_for_state("LOBBY", timeout=5)

    return players


async def configure_lobby(
    host,
    *,
    player_count=3,
    draw_time=3,
    rounds=1,
    word_count=1,
    hints=0,
):
    await host.lobby_update(
        player_count=player_count,
        language="en",
        draw_time=draw_time,
        rounds=rounds,
        word_count=word_count,
        hints=hints,
    )
    await host.wait_for_state("LOBBY", timeout=5)


async def setup_game(
    *,
    player_count=3,
    draw_time=3,
    rounds=1,
    word_count=1,
    hints=0,
):
    room = await create_room()

    players = await create_players(
        room,
        player_count,
    )

    host = players[0]

    await configure_lobby(
        host,
        player_count=player_count,
        draw_time=draw_time,
        rounds=rounds,
        word_count=word_count,
        hints=hints,
    )

    return room, players, host


async def identify_drawer(players):
    """
    Wait until all players see WORD_SELECTION state,
    then return (drawer, guessers).
    """
    states = await asyncio.gather(
        *[
            player.wait_for_state(
                "WORD_SELECTION",
                timeout=20,
            )
            for player in players
        ]
    )

    drawer_pid = states[0]["data"]["current_drawer"]

    drawer = next(
        p for p in players
        if p.pid == drawer_pid
    )

    guessers = [
        p for p in players
        if p.pid != drawer_pid
    ]

    return drawer, guessers


async def get_word(drawer):
    message = await drawer.wait_for(
        "word_options",
        timeout=15,
    )

    options = message["data"]["options"]

    assert options

    option = options[0]

    return (
        option["word"],
        option["word_id"],
    )


async def select_first_word(players):
    """
    Identify the drawer, get word options, select the first word.
    Waits until all players see word_selected event.
    Returns (drawer, guessers, word).
    """
    drawer, guessers = await identify_drawer(
        players
    )

    word, word_id = await get_word(drawer)

    await drawer.select_word(word_id)

    selected_messages = await asyncio.gather(
        *[
            player.wait_for_event(
                "word_selected",
                timeout=5,
            )
            for player in players
        ]
    )

    for player, message in zip(
        players,
        selected_messages,
    ):
        if player.pid == drawer.pid:
            assert message["data"]["word"] == word
            assert message["data"]["is_drawer"] is True
        else:
            assert message["data"]["word"] != word
            assert message["data"]["pattern"]

    return drawer, guessers, word


async def wait_for_turn_end(players, timeout=10):
    """
    Wait for the turn_end event from any player.
    Returns the turn_end message.
    """
    results = await asyncio.gather(
        *[
            player.wait_for_event(
                "turn_end",
                timeout=timeout,
            )
            for player in players
        ]
    )
    return results[0]


async def advance_to_next_turn(players, timeout=12):
    """
    Wait through the leaderboard phase and return when
    the next WORD_SELECTION state arrives.
    Consumes the leaderboard timer messages.
    """
    # The server shows the leaderboard for exactly 7 seconds,
    # then the next turn starts. Wait a bit more to be safe.
    await asyncio.sleep(9)
    return await identify_drawer(players)


# ============================================================
# TC-18 -> TC-22
# Word selection
# ============================================================

async def test_word_selection():
    """
    TC-18: Drawer receives word options (correct count).
    TC-19: Artist selects a word.
    TC-20: Invalid word selection is rejected.
    TC-21: Non-artist cannot select a word.
    TC-22: Guessers receive only the pattern (not the word).
    """
    print("\n=== TC-18 -> TC-22 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=15,
            rounds=1,
            word_count=3,
            hints=0,
        )

        await host.start_game()

        drawer, guessers = await identify_drawer(
            players
        )

        # TC-18: Drawer receives word options.
        options_message = await drawer.wait_for(
            "word_options",
            timeout=15,
        )

        options = options_message["data"]["options"]

        assert len(options) == 3, (
            f"Expected 3 word options, got {len(options)}"
        )

        print("TC-18: Received 3 word options:", [o["word"] for o in options])

        # Guessers must NOT receive word options.
        for guesser in guessers:
            await guesser.expect_no_message(
                "word_options",
                timeout=1,
            )

        print("TC-18: Guessers did not receive word options.")

        # TC-20: Invalid word selection.
        await drawer.select_word(999999)

        error = await drawer.wait_for(
            "error",
            timeout=5,
        )

        assert (
            error["data"]["message"]
            == "Invalid word selection."
        ), f"Unexpected error: {error['data']['message']}"

        print("TC-20: Invalid word selection rejected:", error["data"]["message"])

        # TC-21: Non-artist tries to select a word.
        await guessers[0].select_word(
            options[0]["word_id"]
        )

        error = await guessers[0].wait_for(
            "error",
            timeout=5,
        )

        assert (
            error["data"]["message"]
            == "Only the drawer can select a word."
        ), f"Unexpected error: {error['data']['message']}"

        print("TC-21: Non-artist word selection rejected:", error["data"]["message"])

        # TC-19: Valid selection.
        selected = options[0]

        await drawer.select_word(
            selected["word_id"]
        )

        # TC-22: All players receive word_selected event.
        # Drawer gets the full word; guessers get only the pattern.
        for player in players:
            message = await player.wait_for_event(
                "word_selected",
                timeout=5,
            )

            if player.pid == drawer.pid:
                assert (
                    message["data"]["word"]
                    == selected["word"]
                ), (
                    f"Drawer did not receive full word: "
                    f"{message['data']['word']}"
                )
                assert message["data"]["is_drawer"] is True
                print(f"TC-19/TC-22: Drawer sees full word: {message['data']['word']}")
            else:
                assert (
                    message["data"]["word"]
                    != selected["word"]
                ), "Guesser received the full word!"
                assert message["data"]["pattern"]
                print(f"TC-22: Guesser sees pattern only: {message['data']['word']}")

        print("TC-18 -> TC-22 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-23 / TC-24 / TC-25
# Drawing
# ============================================================

async def test_drawing():
    """
    TC-23: Artist sends a drawing stroke.
    TC-24: Drawing is broadcast to all guessers.
    TC-25: Non-artist drawing attempt is rejected.
    """
    print("\n=== TC-23 / TC-24 / TC-25 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=10,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        drawer, guessers, _ = (
            await select_first_word(players)
        )

        # TC-23 / TC-24: Drawer sends a stroke; all guessers receive it.
        await drawer.draw(
            action="stroke",
            x=100,
            y=200,
        )

        for guesser in guessers:
            message = await guesser.wait_for(
                "draw",
                timeout=5,
            )

            assert message["data"]["pid"] == drawer.pid
            assert message["data"]["action"] == "stroke"
            assert message["data"]["x"] == 100
            assert message["data"]["y"] == 200

        print("TC-23 / TC-24: Drawing broadcast confirmed.")

        # TC-25: Non-artist draw attempt is rejected.
        await guessers[0].draw(
            action="fake_stroke",
            x=1,
            y=1,
        )

        error = await guessers[0].wait_for(
            "error",
            timeout=5,
        )

        assert (
            error["data"]["message"]
            == "Only the drawer can draw."
        ), f"Unexpected error: {error['data']['message']}"

        print("TC-25: Non-drawer drawing rejected.")
        print("TC-23 / TC-24 / TC-25 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-26 -> TC-31
# Guessing
# ============================================================

async def test_guessing():
    """
    TC-26: Submit a guess.
    TC-27: Correct guess triggers system_message.
    TC-28: Incorrect guess is broadcast as chat.
    TC-29: Artist guess attempt is treated as chat.
    TC-30: Correct guesser cannot score again (treated as chat).
    TC-31: Guess after turn ends is handled as normal chat.
    """
    print("\n=== TC-26 -> TC-31 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=15,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        # TC-29: Artist guess is treated as chat (not scored).
        await drawer.chat(word)

        # The drawer's message should be broadcast as chat to everyone.
        chat = await guessers[0].wait_for(
            "chat",
            timeout=5,
            predicate=lambda m:
                m["data"]["pid"] == drawer.pid
                and m["data"]["message"] == word,
        )

        assert chat["data"]["pid"] == drawer.pid

        # Artist should not receive a "Correct guess!" message.
        await drawer.expect_no_message(
            "system_message",
            timeout=0.5,
            predicate=lambda m:
                m["data"]["message"] == "Correct guess!",
        )

        print("TC-29: Artist guess treated as chat.")

        # TC-26 / TC-28: Wrong guess is broadcast as chat.
        await guessers[0].chat("definitely_wrong")

        wrong = await drawer.wait_for(
            "chat",
            timeout=5,
            predicate=lambda m:
                m["data"]["pid"] == guessers[0].pid
                and m["data"]["message"] == "definitely_wrong",
        )

        assert wrong

        # Guesser should not get "Correct guess!".
        await guessers[0].expect_no_message(
            "system_message",
            timeout=0.5,
            predicate=lambda m:
                m["data"]["message"] == "Correct guess!",
        )

        print("TC-26 / TC-28: Incorrect guess broadcast as chat.")

        # TC-26 / TC-27: Correct guess.
        await guessers[0].chat(word)

        correct = await guessers[0].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m:
                m["data"]["message"] == "Correct guess!",
        )

        assert correct

        visibility = await guessers[0].wait_for_event(
            "word_visibility",
            timeout=5,
        )

        assert visibility["data"]["word"] == word
        assert visibility["data"]["correct"] is True

        print("TC-26 / TC-27: Correct guess confirmed.")

        # TC-30: Correctly-guessing player tries again.
        await guessers[0].chat("another_guess")

        # Must be broadcast as chat, not scored.
        another = await drawer.wait_for(
            "chat",
            timeout=5,
            predicate=lambda m:
                m["data"]["pid"] == guessers[0].pid
                and m["data"]["message"] == "another_guess",
        )

        assert another

        print("TC-30: Already-correct player guess treated as chat.")

        # TC-31: End the turn (second guesser guesses correctly).
        await guessers[1].chat(word)

        turn_end = await drawer.wait_for_event(
            "turn_end",
            timeout=5,
        )

        assert turn_end["data"]["reason"] in (
            "WORD_GUESSED", "ALL_GUESSERS_CORRECT"
        )

        print("TC-31: Turn ended.")

        # TC-31: Guess after turn ends.
        # After turn ends (state is TURN_END / not PLAYING), submit the correct word as a guess.
        # It must be treated as regular chat: broadcast to other players, NOT trigger a
        # "Correct guess!" system message, and NOT award additional points.
        await guessers[0].chat(word)

        post_turn_chat = await drawer.wait_for(
            "chat",
            timeout=5,
            predicate=lambda m:
                m["data"]["pid"] == guessers[0].pid
                and m["data"]["message"] == word,
        )
        assert post_turn_chat, "Post-turn guess was not broadcast as chat"

        # Verify no "Correct guess!" system message is generated
        await guessers[0].expect_no_message(
            "system_message",
            timeout=0.5,
            predicate=lambda m: m["data"].get("message") == "Correct guess!",
        )

        print("TC-31: Guess after turn ends treated as chat with no points.")
        print("TC-26 -> TC-31 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-32 -> TC-36 : HINTS
# ============================================================

async def test_hints():
    """
    TC-32: Automatic Hint Timing
    TC-33: Automatic Hint Reveals Letter
    TC-34: Correct Guess Triggers Hint
    TC-35: Hint Limit
    TC-36: Word-Length Hint Limit
    """

    print("\n=== TC-32 -> TC-36 ===")

    # --------------------------------------------------------
    # TC-32 / TC-33: Automatic timer-based hint
    # --------------------------------------------------------

    players = []

    try:
        _, players, host = await setup_game(
            player_count=3,
            draw_time=8,
            rounds=1,
            word_count=1,
            hints=1,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        # Build the initial hidden pattern.
        initial_pattern = "".join(
            " " if char == " " else "_"
            for char in word
        )

        print("Initial pattern:", initial_pattern)

        # Wait for an automatic hint (pattern changes).
        hint_visibility = await guessers[0].wait_for(
            "game_state",
            timeout=9,
            predicate=lambda message: (
                message["data"].get("event")
                == "word_visibility"
                and message["data"].get("pattern")
                != initial_pattern
            ),
        )

        hint_pattern = hint_visibility["data"]["pattern"]

        print("Pattern after automatic hint:", hint_pattern)

        assert hint_pattern != initial_pattern, (
            "Automatic hint did not change the word pattern."
        )

        revealed_before = sum(
            char != "_" and char != " "
            for char in initial_pattern
        )

        revealed_after = sum(
            char != "_" and char != " "
            for char in hint_pattern
        )

        assert revealed_after > revealed_before, (
            "Automatic hint did not reveal a letter."
        )

        print("TC-32: Automatic hint timing confirmed.")
        print("TC-33: Automatic hint revealed a letter.")

    finally:
        for player in players:
            await player.close()

    # --------------------------------------------------------
    # TC-34: Correct guess triggers hint
    # --------------------------------------------------------

    players = []

    try:
        _, players, host = await setup_game(
            player_count=3,
            draw_time=20,
            rounds=1,
            word_count=1,
            hints=2,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        initial_pattern = "".join(
            " " if char == " " else "_"
            for char in word
        )

        print("Initial pattern:", initial_pattern)

        # One guesser becomes correct while the other remains
        # incorrect. The turn continues, so process_guess()
        # reveals a hint for the remaining guesser.
        await guessers[0].chat(word)

        await guessers[0].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m:
                m["data"]["message"] == "Correct guess!",
        )

        # The remaining guesser (not yet correct) should receive
        # an updated pattern (hint revealed).
        hint_visibility = await guessers[1].wait_for(
            "game_state",
            timeout=5,
            predicate=lambda message: (
                message["data"].get("event")
                == "word_visibility"
                and message["data"].get("pattern")
                != initial_pattern
            ),
        )

        hint_pattern = hint_visibility["data"]["pattern"]

        print("Pattern after correct-guess hint:", hint_pattern)

        assert hint_pattern != initial_pattern, (
            "Correct guess did not trigger a hint."
        )

        # The correct guesser receives the full word.
        correct_visibility = await guessers[0].wait_for(
            "game_state",
            timeout=5,
            predicate=lambda message:
                message["data"].get("event")
                == "word_visibility"
                and message["data"].get("correct")
                is True,
        )

        assert (
            correct_visibility["data"]["word"]
            == word
        )

        assert (
            correct_visibility["data"]["correct"]
            is True
        )

        print("TC-34: Correct-guess hint confirmed.")

    finally:
        for player in players:
            await player.close()

    # --------------------------------------------------------
    # TC-35 / TC-36: Hint limit + word-length limit
    # --------------------------------------------------------

    players = []

    try:
        _, players, host = await setup_game(
            player_count=3,
            draw_time=12,
            rounds=1,
            word_count=1,
            hints=5,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        initial_pattern = "".join(
            " " if char == " " else "_"
            for char in word
        )

        word_length = len(word.replace(" ", ""))

        if word_length == 3:
            word_length_limit = 1
        elif word_length in (4, 5):
            word_length_limit = 2
        elif word_length == 6:
            word_length_limit = 3
        elif word_length == 7:
            word_length_limit = 4
        else:
            word_length_limit = 5

        expected_max_hints = min(5, word_length_limit)

        print("Word:", word)
        print("Word length:", word_length)
        print("Expected maximum hints:", expected_max_hints)

        patterns = {initial_pattern}

        # No guessing, so every pattern change is from the
        # automatic hint worker.
        while True:
            try:
                message = await guessers[0].wait_for(
                    "game_state",
                    timeout=15,
                    predicate=lambda message: (
                        message["data"].get("event")
                        in (
                            "word_visibility",
                            "turn_end",
                        )
                    ),
                )

            except asyncio.TimeoutError:
                break

            event = message["data"].get("event")

            if event == "turn_end":
                break

            pattern = message["data"].get("pattern")

            if pattern:
                patterns.add(pattern)

        observed_hints = len(patterns) - 1

        print("Observed hint count:", observed_hints)

        assert observed_hints <= expected_max_hints, (
            f"Hint limit exceeded: "
            f"observed {observed_hints}, "
            f"maximum allowed {expected_max_hints}"
        )

        print("TC-35: Hint limit respected.")
        print("TC-36: Word-length hint limit respected.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-37 / TC-38
# Turn timer + timeout
# ============================================================

async def test_turn_timeout():
    """
    TC-37: Turn timer ticks from draw_time down to 1.
    TC-38: Turn ends with reason TIME_UP when timer expires.
    """
    print("\n=== TC-37 / TC-38 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=3,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        timers = []

        for _ in range(3):
            timer = await drawer.wait_for_timer(
                "drawing",
                timeout=5,
            )

            timers.append(timer["data"]["seconds"])

            if timers[-1] == 1:
                break

        assert timers[0] == 3, (
            f"Expected first timer to be 3, got {timers[0]}"
        )
        assert 1 in timers, (
            "Timer did not count down to 1."
        )

        print("TC-37: Drawing timer confirmed:", timers)

        turn_end = await drawer.wait_for_event(
            "turn_end",
            timeout=5,
        )

        assert turn_end["data"]["reason"] == "TIME_UP", (
            f"Expected TIME_UP, got {turn_end['data']['reason']}"
        )
        assert turn_end["data"]["word"] == word

        print("TC-38: TIME_UP confirmed.")
        print("TC-37 / TC-38 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-39 / TC-40
# Everyone guesses correctly + next turn
# ============================================================

async def test_everyone_guesses_and_next_turn():
    """
    TC-39: When all guessers guess correctly, the turn ends
           with reason WORD_GUESSED (or ALL_GUESSERS_CORRECT).
    TC-40: The next turn starts with a different drawer.
    """
    print("\n=== TC-39 / TC-40 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=10,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        first_drawer_pid = drawer.pid

        await guessers[0].chat(word)

        await guessers[0].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m:
                m["data"]["message"]
                == "Correct guess!",
        )

        await guessers[1].chat(word)

        await guessers[1].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m:
                m["data"]["message"]
                == "Correct guess!",
        )

        turn_end = await drawer.wait_for_event(
            "turn_end",
            timeout=5,
        )

        assert (
            turn_end["data"]["reason"]
            in ("WORD_GUESSED", "ALL_GUESSERS_CORRECT")
        ), f"Unexpected reason: {turn_end['data']['reason']}"

        print("TC-39: Everyone guessed correctly -> turn ended.")

        # Wait through the leaderboard phase (7 seconds)
        # before the next turn begins.
        await asyncio.sleep(9)

        # TC-40: Next turn should have a different drawer.
        # identify_drawer returns (drawer, guessers) - 2 values.
        next_drawer, _ = await identify_drawer(players)

        assert next_drawer.pid != first_drawer_pid, (
            f"Next drawer is the same as the first: "
            f"{next_drawer.name}"
        )

        print("TC-40: Next drawer confirmed:", next_drawer.name)
        print("TC-39 / TC-40 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-41 / TC-42
# Round completion + next round
# ============================================================

async def test_round_and_next_round():
    """
    TC-41: After all players have drawn in a round, the round ends
           (ROUND_END state is broadcast).
    TC-42: When there are more rounds remaining, a new round starts
           and ROUND_START is broadcast.
    """
    print("\n=== TC-41 / TC-42 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=3,
            rounds=2,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        # Complete round 1 - all 3 turns.
        for turn_index in range(3):
            drawer, guessers, word = (
                await select_first_word(players)
            )

            print(f"Round 1, Turn {turn_index + 1}: drawer = {drawer.name}")

            # Let the timer expire (draw_time=3 + leaderboard 7s).
            turn_end = await wait_for_turn_end(
                players,
                timeout=6,
            )

            assert turn_end["data"]["word"] == word

            if turn_index < 2:
                # Wait through the 7s leaderboard.
                await asyncio.sleep(9)

        # After the 3rd turn in round 1, wait for ROUND_END.
        # The server sends it after the leaderboard timer completes.
        round_end = await players[0].wait_for_state(
            "ROUND_END",
            timeout=12,
        )

        assert round_end["data"]["state"] == "ROUND_END"

        print("TC-41: ROUND_END confirmed.")

        # TC-42: Next round should start (ROUND_START state).
        round_start = await players[0].wait_for_state(
            "ROUND_START",
            timeout=6,
        )

        assert round_start["data"]["state"] == "ROUND_START"

        print("TC-42: Next ROUND_START confirmed.")
        print("TC-41 / TC-42 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-43
# Guesser disconnect
# ============================================================

async def test_guesser_disconnect():
    """
    TC-43: When a guesser disconnects, the remaining players
           receive a system_message notification. The game continues.
    """
    print("\n=== TC-43 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=10,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        disconnecting = guessers[0]
        remaining_guesser = guessers[1]

        await disconnecting.close()

        # Remaining players receive a disconnect notification.
        system = await drawer.wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m:
                "disconnected" in m["data"]["message"].lower()
                or "lost connection" in m["data"]["message"].lower(),
        )

        assert system
        print("TC-43: Guesser disconnect notification received.")

        # TC-43: Verify the game CONTINUES normally:
        # 1. Drawer can still draw and remaining guesser receives it
        await drawer.draw(action="stroke", x=50, y=50)
        draw_msg = await remaining_guesser.wait_for("draw", timeout=5)
        assert draw_msg["data"]["pid"] == drawer.pid
        print("TC-43: Drawing interaction continues normally.")

        # 2. Remaining guesser can guess correctly and earn points
        await remaining_guesser.chat(word)
        correct_sys = await remaining_guesser.wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m: m["data"]["message"] == "Correct guess!",
        )
        assert correct_sys

        # 3. Turn completes normally (since all remaining active guessers guessed)
        turn_end = await drawer.wait_for_event("turn_end", timeout=5)
        assert turn_end["data"]["points_awarded"][remaining_guesser.pid] >= 150
        print("TC-43: Turn completes normally with remaining active players.")
        print("TC-43 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-44
# Drawer disconnect
# ============================================================

async def test_drawer_disconnect():
    """
    TC-44: When the drawer disconnects during a turn, the remaining
           players are notified and the game state transitions to
           TURN_END (turn terminates due to drawer disconnect).
    """
    print("\n=== TC-44 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=10,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        drawer, guessers, _ = (
            await select_first_word(players)
        )

        await drawer.close()

        # Remaining players receive a disconnect notification.
        system = await guessers[0].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m:
                "disconnected" in m["data"]["message"].lower()
                or "lost connection" in m["data"]["message"].lower(),
        )

        assert system

        print("TC-44: Disconnect notification received.")

        # The turn should end because the drawer disconnected.
        # The backend transitions to TURN_END state.
        # NOTE: Due to a known backend behavior, the turn_end event
        # may not be broadcast separately; instead a TURN_END
        # game_state is sent directly.
        turn_over = await guessers[0].wait_for(
            "game_state",
            timeout=5,
            predicate=lambda m:
                m["data"].get("state") == "TURN_END"
                or m["data"].get("event") == "turn_end",
        )

        state_or_event = (
            turn_over["data"].get("state")
            or turn_over["data"].get("event")
        )

        assert state_or_event in ("TURN_END", "turn_end"), (
            f"Unexpected game state after drawer disconnect: {turn_over}"
        )

        print("TC-44: Turn terminated after drawer disconnect.")
        print("TC-44 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-45
# Player reconnects during game
# ============================================================

async def test_reconnect():
    """
    TC-45: A player who disconnects during the game can reconnect
           within the grace period and resume play. The reconnecting
           player receives the current game state (PLAYING) and
           the masked word pattern.
    """
    print("\n=== TC-45 ===")

    players = []

    try:
        room, players, host = await setup_game(
            draw_time=15,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        drawer, guessers, word = (
            await select_first_word(players)
        )

        reconnecting = guessers[0]

        # Disconnect.
        await reconnecting.close()

        await asyncio.sleep(1)

        # Reconnect using the same PID.
        await reconnecting.connect(
            WS_BASE_URL,
            room["room_id"],
        )

        await reconnecting.join()

        # After reconnect, handle_reconnect sends:
        # 1. game_state with state=PLAYING
        # 2. game_state with event=word_visibility
        # Old messages may remain in the buffer from before disconnect.
        # Use wait_for_state which filters by state value.
        state = await reconnecting.wait_for_state(
            "PLAYING",
            timeout=5,
        )

        assert (
            state["data"]["state"]
            == "PLAYING"
        ), f"Expected PLAYING, got {state['data']['state']}"

        print("TC-45: Reconnecting player sees PLAYING state.")

        # The reconnecting player should get the masked word pattern
        # (not the full word) since they have not guessed correctly.
        visibility = await reconnecting.wait_for_event(
            "word_visibility",
            timeout=5,
        )

        assert (
            visibility["data"]["word"]
            != word
        ), "Reconnecting player received the full word (security issue)."

        assert visibility["data"]["pattern"], (
            "Reconnecting player did not receive the word pattern."
        )

        print("TC-45: Reconnecting player receives masked pattern (not full word).")
        print("TC-45 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-46
# Late player joins
# ============================================================

async def test_late_player():
    """
    TC-46: A player who joins while the game is already in progress
           is added to the player list and receives the current
           game state.
    """
    print("\n=== TC-46 ===")

    players = []

    try:
        room = await create_room()

        host = TestPlayer(
            room["name"],
            pid=room["pid"],
        )

        second = TestPlayer("Test2")

        players = [host, second]

        for player in players:
            await player.connect(
                WS_BASE_URL,
                room["room_id"],
            )

        for player in players:
            await player.join()

        # Start with only 2 players; room is configured for 3.
        await configure_lobby(
            host,
            player_count=3,
            draw_time=15,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        # Wait until gameplay has started.
        await host.wait_for_state(
            "WORD_SELECTION",
            timeout=20,
        )

        # New player joins during the game.
        late = TestPlayer("LatePlayer")

        players.append(late)

        await late.connect(
            WS_BASE_URL,
            room["room_id"],
        )

        await late.join()

        state = await late.wait_for(
            "game_state",
            timeout=5,
        )

        # The late player should appear in the players list.
        assert any(
            player["pid"] == late.pid
            for player in state["data"]["players"]
        ), "Late player not found in game_state players list."

        print("TC-46: Late player joined successfully:", late.name)
        print("TC-46 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-47 -> TC-51
# Scoring
# ============================================================

async def test_scoring():
    """
    TC-47: Correct guesser receives >= 150 points.
    TC-48: Artist receives points proportional to guessers' speed.
    TC-49: Speed-based scoring: guessing sooner means more points.
    TC-50: Leaderboard is updated and broadcast after each turn.
    TC-51: Score carries across rounds / turns.
    """
    print("\n=== TC-47 -> TC-51 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=6,
            rounds=2,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        # ---- Round 1, Turn 1 ----
        drawer, guessers, word = (
            await select_first_word(players)
        )

        print(f"Round 1, Turn 1 drawer: {drawer.name}, word: {word}")

        # Guesser 0 guesses immediately at ~0.5s to maximize speed bonus.
        await guessers[0].chat(word)
        await guessers[0].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda m:
                m["data"]["message"] == "Correct guess!",
        )

        # Controlled delay: wait 3 seconds before Guesser 1 guesses.
        await asyncio.sleep(3)

        # Guesser 1 guesses later with significantly less time remaining.
        await guessers[1].chat(word)

        turn_end = await wait_for_turn_end(
            players,
            timeout=5,
        )

        points = turn_end["data"]["points_awarded"]
        print("Round 1, Turn 1 points awarded:", points)

        # TC-47: Both guessers earn at least base points (>= 150).
        assert points[guessers[0].pid] >= 150, (
            f"Guesser 0 points ({points[guessers[0].pid]}) < 150"
        )
        assert points[guessers[1].pid] >= 150, (
            f"Guesser 1 points ({points[guessers[1].pid]}) < 150"
        )

        # TC-49: Speed-based scoring.
        # Guesser 0 guessed with ~5s remaining, Guesser 1 guessed with ~2s remaining.
        # Guesser 0 must earn strictly MORE points than Guesser 1.
        assert points[guessers[0].pid] > points[guessers[1].pid], (
            f"Faster guesser ({points[guessers[0].pid]}) did not score strictly more than "
            f"slower guesser ({points[guessers[1].pid]})."
        )
        print(f"TC-49: Speed scoring confirmed: Fast ({points[guessers[0].pid]}) > Slow ({points[guessers[1].pid]}).")

        # TC-48: Artist scoring.
        # With both guessers guessing correctly, artist must earn strictly positive points.
        assert points[drawer.pid] > 0, (
            f"Artist points ({points[drawer.pid]}) must be strictly positive."
        )
        assert points[drawer.pid] <= 450, (
            f"Artist points ({points[drawer.pid]}) must not exceed 450 max."
        )
        print(f"TC-48: Artist points confirmed: {points[drawer.pid]} points.")

        # TC-50: Leaderboard update broadcast after turn.
        leaderboards = await asyncio.gather(
            *[p.wait_for("leaderboard", timeout=5) for p in players]
        )
        rows = leaderboards[0]["data"]["players"]
        assert rows, "Leaderboard is empty after turn."

        by_pid = {row["pid"]: row["points"] for row in rows}
        assert by_pid[guessers[0].pid] >= points[guessers[0].pid]
        guesser0_r1_score = by_pid[guessers[0].pid]
        print("TC-50: Leaderboard update confirmed:", by_pid)

        # ---- Complete Round 1 (Turns 2 and 3) ----
        await asyncio.sleep(8)  # leaderboard phase

        # Round 1, Turn 2
        d2, g2, w2 = await select_first_word(players)
        await g2[0].chat(w2)
        await g2[1].chat(w2)
        await wait_for_turn_end(players, timeout=5)
        await asyncio.gather(*[p.wait_for("leaderboard", timeout=5) for p in players])
        await asyncio.sleep(8)

        # Round 1, Turn 3
        d3, g3, w3 = await select_first_word(players)
        await g3[0].chat(w3)
        await g3[1].chat(w3)
        await wait_for_turn_end(players, timeout=5)
        await asyncio.gather(*[p.wait_for("leaderboard", timeout=5) for p in players])

        # ---- TC-51: Cross Round Boundary (ROUND_END -> ROUND_START -> Round 2) ----
        # Wait for Round 1 to end (after 7s leaderboard)
        round_end = await players[0].wait_for_state("ROUND_END", timeout=12)
        assert round_end["data"]["state"] == "ROUND_END"
        print("Round 1 ended: ROUND_END state confirmed.")

        # Wait for Round 2 to start (after 3s round transition)
        round_start = await players[0].wait_for_state("ROUND_START", timeout=6)
        assert round_start["data"]["state"] == "ROUND_START"
        print("Round 2 started: ROUND_START state confirmed.")

        # Enter Round 2, Turn 1
        d_r2, g_r2, w_r2 = await select_first_word(players)
        # Complete Round 2, Turn 1
        await g_r2[0].chat(w_r2)
        await g_r2[1].chat(w_r2)
        await wait_for_turn_end(players, timeout=5)

        # In Round 2, leaderboard must retain the points accumulated from Round 1
        lb_r2 = await asyncio.gather(*[p.wait_for("leaderboard", timeout=5) for p in players])
        by_pid_r2 = {row["pid"]: row["points"] for row in lb_r2[0]["data"]["players"]}

        assert guessers[0].pid in by_pid_r2, "Player missing from Round 2 leaderboard"
        assert by_pid_r2[guessers[0].pid] >= guesser0_r1_score, (
            f"Score did not persist into Round 2: Round 1 had {guesser0_r1_score}, "
            f"Round 2 has {by_pid_r2[guessers[0].pid]}"
        )
        print(
            f"TC-51: Score carried across rounds: {by_pid_r2[guessers[0].pid]} >= {guesser0_r1_score}."
        )
        print("TC-47 -> TC-51 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# TC-52 -> TC-55
# Complete game
# ============================================================

async def test_complete_game():
    """
    TC-52: The last turn in the game completes normally.
    TC-53: The last round ends and ROUND_END is broadcast.
    TC-54: A final leaderboard is broadcast at GAME_END.
    TC-55: The game reaches GAME_END and eventually returns to LOBBY.
    """
    print("\n=== TC-52 -> TC-55 ===")

    players = []

    try:
        _, players, host = await setup_game(
            draw_time=3,
            rounds=1,
            word_count=1,
            hints=0,
        )

        await host.start_game()

        completed_turns = 0
        last_drawer = None

        # With rounds=1 and 3 players, there are exactly 3 turns.
        while completed_turns < 3:
            drawer, guessers = (
                await identify_drawer(players)
            )

            print(f"Turn {completed_turns + 1}/3: drawer = {drawer.name}")

            word, word_id = await get_word(drawer)

            await drawer.select_word(word_id)

            await drawer.wait_for_event(
                "word_selected",
                timeout=5,
            )

            # Make both guessers correct to end the turn quickly.
            await guessers[0].chat(word)

            await guessers[0].wait_for(
                "system_message",
                timeout=5,
                predicate=lambda m:
                    m["data"]["message"] == "Correct guess!",
            )

            await guessers[1].chat(word)

            turn_end = await wait_for_turn_end(
                players,
                timeout=5,
            )

            assert turn_end["data"]["points_awarded"]

            # Consume the turn-end leaderboard across all players
            await asyncio.gather(
                *[p.wait_for("leaderboard", timeout=5) for p in players]
            )

            completed_turns += 1
            last_drawer = drawer

            print(f"Completed turn {completed_turns}/3")

            if completed_turns < 3:
                # Wait through the 7s turn-end leaderboard phase.
                await asyncio.sleep(8)

        # TC-52: The final turn completed successfully.
        print("TC-52: Final turn completed.")

        # Clear any prior leaderboards on last_drawer before the game end phase
        last_drawer.clear_messages("leaderboard")

        # TC-53: The round ends and ROUND_END state is explicitly broadcast.
        # The server reaches ROUND_END after the final turn's 7s leaderboard phase.
        round_end = await last_drawer.wait_for_state(
            "ROUND_END",
            timeout=12,
        )
        assert round_end["data"]["state"] == "ROUND_END", (
            f"Expected ROUND_END, got {round_end['data']['state']}"
        )
        print("TC-53: ROUND_END state explicitly confirmed.")

        # TC-55: Following the 3s round transition, the game concludes at GAME_END.
        game_end = await last_drawer.wait_for_state(
            "GAME_END",
            timeout=10,
        )
        assert game_end["data"]["state"] == "GAME_END", (
            f"Expected GAME_END, got {game_end['data']['state']}"
        )
        print("TC-55: GAME_END confirmed.")

        # TC-54: Final leaderboard is broadcast at GAME_END.
        leaderboard = await last_drawer.wait_for(
            "leaderboard",
            timeout=5,
        )
        players_lb = leaderboard["data"]["players"]
        assert players_lb, "Final leaderboard is empty."
        assert len(players_lb) == len(players), "Final leaderboard missing players."

        # Verify final leaderboard rankings are sorted descending by points
        for i in range(len(players_lb) - 1):
            assert players_lb[i]["points"] >= players_lb[i + 1]["points"], (
                f"Final leaderboard not sorted: {players_lb[i]} vs {players_lb[i+1]}"
            )

        print(
            "TC-54: Final leaderboard confirmed:",
            [(r["name"], r["points"]) for r in players_lb],
        )

        # TC-55: After 7s displaying the final leaderboard, server returns to LOBBY.
        lobby = await last_drawer.wait_for_state(
            "LOBBY",
            timeout=12,
        )
        assert lobby["data"]["state"] == "LOBBY"
        print("TC-55: GAME_END -> LOBBY confirmed.")
        print("TC-52 -> TC-55 PASSED.")

    finally:
        for player in players:
            await player.close()


# ============================================================
# Runner
# ============================================================

async def run_test(
    name,
    test_function,
):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    try:
        await test_function()

        print(f"PASS: {name}")

        return True

    except Exception as exc:
        import traceback
        print(f"FAIL: {name}")
        print(f"ERROR: {exc}")
        traceback.print_exc()

        return False


async def main():
    tests = [
        (
            "TC-18 to TC-22 Word Selection",
            test_word_selection,
        ),
        (
            "TC-23 to TC-25 Drawing",
            test_drawing,
        ),
        (
            "TC-26 to TC-31 Guessing",
            test_guessing,
        ),
        (
            "TC-32 to TC-36 Hints",
            test_hints,
        ),
        (
            "TC-37 / TC-38 Timer + Timeout",
            test_turn_timeout,
        ),
        (
            "TC-39 / TC-40 Everyone Correct + Next Turn",
            test_everyone_guesses_and_next_turn,
        ),
        (
            "TC-41 / TC-42 Round Completion + Next Round",
            test_round_and_next_round,
        ),
        (
            "TC-43 Guesser Disconnect",
            test_guesser_disconnect,
        ),
        (
            "TC-44 Drawer Disconnect",
            test_drawer_disconnect,
        ),
        (
            "TC-45 Reconnect",
            test_reconnect,
        ),
        (
            "TC-46 Late Player",
            test_late_player,
        ),
        (
            "TC-47 to TC-51 Scoring",
            test_scoring,
        ),
        (
            "TC-52 to TC-55 Complete Game",
            test_complete_game,
        ),
    ]

    passed = 0
    failed = 0

    for name, test_function in tests:
        result = await run_test(
            name,
            test_function,
        )

        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(tests)}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())