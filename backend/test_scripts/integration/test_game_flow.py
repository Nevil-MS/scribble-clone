import asyncio
import httpx

from websocket_client import TestPlayer


HTTP_BASE_URL = "http://127.0.0.1:8000"
WS_BASE_URL = "ws://127.0.0.1:8000"


async def create_room():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{HTTP_BASE_URL}/rooms"
        )

    assert response.status_code == 200, (
        f"Room creation failed: "
        f"{response.status_code} {response.text}"
    )

    return response.json()


async def setup_room(
    draw_time=3,
    rounds=1,
    word_count=1,
    hints=0,
):
    room = await create_room()

    host = TestPlayer(
        room["name"],
        pid=room["pid"],
    )

    player_b = TestPlayer("TestB")
    player_c = TestPlayer("TestC")

    players = [host, player_b, player_c]

    for player in players:
        await player.connect(
            WS_BASE_URL,
            room["room_id"],
        )

    for player in players:
        await player.join()

    await host.lobby_update(
        player_count=3,
        language="en",
        draw_time=draw_time,
        rounds=rounds,
        word_count=word_count,
        hints=hints,
    )

    return room, players, host


async def identify_drawer(players):
    states = await asyncio.gather(
        *[
            player.wait_for_state(
                "WORD_SELECTION",
                timeout=10,
            )
            for player in players
        ]
    )

    drawer_pid = states[0]["data"]["current_drawer"]

    drawer = next(
        player
        for player in players
        if player.pid == drawer_pid
    )

    guessers = [
        player
        for player in players
        if player.pid != drawer_pid
    ]

    return drawer, guessers, states


async def run_turn(
    players,
    host,
    *,
    perform_guess=True,
    wait_for_timeout=False,
):
    drawer, guessers, states = await identify_drawer(players)

    print(f"Drawer: {drawer.name}")
    print(
        f"Guessers: "
        f"{[player.name for player in guessers]}"
    )

    # Only drawer should receive options.
    options_message = await drawer.wait_for(
        "word_options",
        timeout=10,
    )

    options = options_message["data"]["options"]

    assert len(options) >= 1

    selected = options[0]
    selected_word = selected["word"]
    selected_word_id = selected["word_id"]

    print(f"Selected word: {selected_word}")

    # Guessers must not receive word options.
    for guesser in guessers:
        await guesser.expect_no_message(
            "word_options",
            timeout=0.5,
        )

    await drawer.select_word(selected_word_id)

    # All players receive word_selected.
    selected_messages = await asyncio.gather(
        *[
            player.wait_for_event(
                "word_selected",
                timeout=5,
            )
            for player in players
        ]
    )

    drawer_message = next(
        message
        for player, message in zip(players, selected_messages)
        if player.pid == drawer.pid
    )

    assert drawer_message["data"]["word"] == selected_word
    assert drawer_message["data"]["is_drawer"] is True

    # Verify guessers only receive pattern.
    for player, message in zip(players, selected_messages):
        if player.pid == drawer.pid:
            continue

        assert message["data"]["word"] != selected_word
        assert message["data"]["pattern"]

    print("Word privacy confirmed.")

    await drawer.draw(
        action="stroke",
        x=100,
        y=100,
    )

    draw_message = await guessers[0].wait_for(
        "draw",
        timeout=5,
    )

    assert draw_message["data"]["pid"] == drawer.pid
    assert draw_message["data"]["action"] == "stroke"

    print("Drawing broadcast confirmed.")

    if wait_for_timeout:
        turn_end = await drawer.wait_for_event(
            "turn_end",
            timeout=10,
        )

        assert turn_end["data"]["reason"] == "TIME_UP"

        return {
            "drawer": drawer,
            "guessers": guessers,
            "word": selected_word,
            "turn_end": turn_end,
        }

    if perform_guess:
        # First guesser gives an incorrect answer.
        await guessers[1].chat(
            "definitely_not_the_word"
        )

        wrong_chat = await drawer.wait_for(
            "chat",
            timeout=5,
            predicate=lambda message:
                message["data"]["pid"] == guessers[1].pid
        )

        assert (
            wrong_chat["data"]["message"]
            == "definitely_not_the_word"
        )

        print("Incorrect guess confirmed.")

        # First guesser guesses correctly.
        await guessers[0].chat(selected_word)

        await guessers[0].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda message:
                message["data"]["message"]
                == "Correct guess!",
        )

        visibility = await guessers[0].wait_for_event(
            "word_visibility",
            timeout=5,
            predicate=lambda message:
                message.get("data", {}).get("word") == selected_word,
        )

        assert visibility["data"]["word"] == selected_word
        assert visibility["data"]["correct"] is True

        print("Correct guess confirmed.")

        # Second guesser remains incorrect.
        # Now let them guess correctly too.
        await guessers[1].chat(selected_word)
        await guessers[1].wait_for(
            "system_message",
            timeout=5,
            predicate=lambda message:
                message["data"]["message"] == "Correct guess!",
        )

        turn_ends = await asyncio.gather(
            *[p.wait_for_event("turn_end", timeout=5) for p in players]
        )
        turn_end = turn_ends[0]

        assert turn_end["data"]["reason"] == "WORD_GUESSED"

        print("All guessers correct -> turn ended.")

    else:
        turn_ends = await asyncio.gather(
            *[p.wait_for_event("turn_end", timeout=10) for p in players]
        )
        turn_end = turn_ends[0]

    points = turn_end["data"]["points_awarded"]

    assert isinstance(points, dict)

    leaderboards = await asyncio.gather(
        *[p.wait_for("leaderboard", timeout=5) for p in players]
    )
    leaderboard = leaderboards[0]

    assert leaderboard["data"]["players"]

    print("Points:", points)
    print("Leaderboard:", leaderboard["data"])

    return {
        "drawer": drawer,
        "guessers": guessers,
        "word": selected_word,
        "turn_end": turn_end,
        "leaderboard": leaderboard,
    }


async def main():
    room = None
    players = []

    try:
        room, players, host = await setup_room(
            draw_time=3,
            rounds=1,
            word_count=1,
            hints=0,
        )

        print(
            f"Room created: {room['room_id']}"
        )

        await host.start_game()

        print("Game started.")

        # One round with three players = three turns.
        for turn_number in range(1, 4):
            print(f"\n--- Turn {turn_number}/3 ---")

            result = await run_turn(
                players,
                host,
                perform_guess=True,
            )

            first_drawer = result["drawer"]

            print(f"Turn {turn_number} completed.")

            # The backend spends 7 seconds in TURN_END
            # before advancing to the next turn.
            if turn_number < 3:
                await asyncio.sleep(8)

        # After the third and final turn, the game should reach GAME_END.
        game_end = await first_drawer.wait_for_state(
            "GAME_END",
            timeout=15,
        )

        assert game_end["data"]["state"] == "GAME_END"

        print("GAME_END confirmed.")

        await first_drawer.wait_for(
            "leaderboard",
            timeout=5,
        )

        # Final leaderboard timer.
        await asyncio.sleep(8)

        lobby = await first_drawer.wait_for_state(
            "LOBBY",
            timeout=5,
        )

        assert lobby["data"]["state"] == "LOBBY"

        print("Returned to LOBBY.")
        print("\nFULL GAME FLOW PASSED.")

    finally:
        for player in players:
            await player.close()


if __name__ == "__main__":
    asyncio.run(main())