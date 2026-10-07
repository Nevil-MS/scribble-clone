"""
Debug script to understand specific test failures.
Runs targeted versions of the failing tests and prints full tracebacks.
"""
import asyncio
import httpx
import traceback

from websocket_client import TestPlayer


HTTP_BASE_URL = "http://127.0.0.1:8000"
WS_BASE_URL = "ws://127.0.0.1:8000"


async def create_room():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{HTTP_BASE_URL}/rooms")
    assert response.status_code == 200
    return response.json()


async def create_players(room, count=3):
    players = [TestPlayer(room["name"], pid=room["pid"])]
    for index in range(1, count):
        players.append(TestPlayer(f"Test{index + 1}"))
    for player in players:
        await player.connect(WS_BASE_URL, room["room_id"])
    for player in players:
        await player.join()
    return players


async def configure_lobby(host, *, player_count=3, draw_time=3, rounds=1, word_count=1, hints=0):
    await host.lobby_update(
        player_count=player_count,
        language="en",
        draw_time=draw_time,
        rounds=rounds,
        word_count=word_count,
        hints=hints,
    )


async def setup_game(*, player_count=3, draw_time=3, rounds=1, word_count=1, hints=0):
    room = await create_room()
    players = await create_players(room, player_count)
    host = players[0]
    await configure_lobby(host, player_count=player_count, draw_time=draw_time,
                           rounds=rounds, word_count=word_count, hints=hints)
    return room, players, host


async def identify_drawer(players):
    states = await asyncio.gather(
        *[player.wait_for_state("WORD_SELECTION", timeout=15) for player in players]
    )
    drawer_pid = states[0]["data"]["current_drawer"]
    drawer = next(p for p in players if p.pid == drawer_pid)
    guessers = [p for p in players if p.pid != drawer_pid]
    return drawer, guessers


async def select_first_word(players):
    drawer, guessers = await identify_drawer(players)
    message = await drawer.wait_for("word_options", timeout=10)
    options = message["data"]["options"]
    option = options[0]
    word, word_id = option["word"], option["word_id"]
    await drawer.select_word(word_id)
    selected_messages = await asyncio.gather(
        *[player.wait_for_event("word_selected", timeout=5) for player in players]
    )
    return drawer, guessers, word


# ============================================================
# Debug TC-39/TC-40
# ============================================================

async def debug_tc40():
    print("\n=== DEBUG TC-40 ===")
    players = []
    try:
        _, players, host = await setup_game(draw_time=10, rounds=1, word_count=1, hints=0)
        await host.start_game()

        drawer, guessers, word = await select_first_word(players)
        print(f"Turn 1 drawer: {drawer.name}")

        await guessers[0].chat(word)
        await guessers[0].wait_for("system_message", timeout=5,
                                   predicate=lambda m: m["data"]["message"] == "Correct guess!")
        await guessers[1].chat(word)
        await guessers[1].wait_for("system_message", timeout=5,
                                   predicate=lambda m: m["data"]["message"] == "Correct guess!")

        turn_end = await drawer.wait_for_event("turn_end", timeout=5)
        print(f"turn_end reason: {turn_end['data']['reason']}")
        assert turn_end["data"]["reason"] == "WORD_GUESSED"
        print("TC-39 passed.")

        # Wait through leaderboard phase
        await asyncio.sleep(8)

        # Next turn - identify_drawer returns (drawer, guessers) - 2 values!
        result = await identify_drawer(players)
        print(f"identify_drawer returned {len(result)} values: {result}")
        next_drawer = result[0]
        print(f"Next drawer: {next_drawer.name}")
        assert next_drawer.pid != drawer.pid
        print("TC-40 passed.")

    except Exception:
        traceback.print_exc()
    finally:
        for player in players:
            await player.close()


# ============================================================
# Debug TC-44 Drawer Disconnect
# ============================================================

async def debug_tc44():
    print("\n=== DEBUG TC-44 ===")
    players = []
    try:
        _, players, host = await setup_game(draw_time=10, rounds=1, word_count=1, hints=0)
        await host.start_game()

        drawer, guessers, _ = await select_first_word(players)
        print(f"Drawer: {drawer.name}")

        await drawer.close()
        print("Drawer closed.")

        # Wait for system message
        try:
            system = await guessers[0].wait_for(
                "system_message",
                timeout=5,
                predicate=lambda m: "drawer disconnected" in m["data"]["message"].lower(),
            )
            print(f"System message received: {system['data']['message']}")
        except asyncio.TimeoutError:
            print("TIMEOUT: No 'drawer disconnected' system_message received in 5 seconds")
            # Let's see all messages
            print(f"guessers[0] messages: {guessers[0].messages}")

        # Wait for turn_end event
        try:
            turn_end = await guessers[0].wait_for_event("turn_end", timeout=5)
            print(f"turn_end received: reason={turn_end['data']['reason']}")
        except asyncio.TimeoutError:
            print("TIMEOUT: No turn_end event in 5 seconds")
            print(f"guessers[0] messages: {guessers[0].messages}")

    except Exception:
        traceback.print_exc()
    finally:
        for player in players:
            await player.close()


# ============================================================
# Debug TC-45 Reconnect
# ============================================================

async def debug_tc45():
    print("\n=== DEBUG TC-45 ===")
    players = []
    try:
        room, players, host = await setup_game(draw_time=10, rounds=1, word_count=1, hints=0)
        await host.start_game()

        drawer, guessers, word = await select_first_word(players)
        reconnecting = guessers[0]

        await reconnecting.close()
        print("Disconnected player.")
        await asyncio.sleep(1)

        await reconnecting.connect(WS_BASE_URL, room["room_id"])
        print("Reconnected.")
        await reconnecting.join()
        print("Joined.")

        # Wait for game_state
        try:
            state = await reconnecting.wait_for("game_state", timeout=5)
            print(f"game_state received: state={state['data'].get('state')}")
            assert state["data"]["state"] == "PLAYING"
        except asyncio.TimeoutError:
            print("TIMEOUT: No game_state in 5 seconds")
            print(f"Messages so far: {reconnecting.messages}")

        try:
            visibility = await reconnecting.wait_for_event("word_visibility", timeout=5)
            print(f"word_visibility: {visibility['data']}")
            assert visibility["data"]["word"] != word
            print("TC-45 passed.")
        except asyncio.TimeoutError:
            print("TIMEOUT: No word_visibility event in 5 seconds")
            print(f"Messages so far: {reconnecting.messages}")

    except Exception:
        traceback.print_exc()
    finally:
        for player in players:
            await player.close()


# ============================================================
# Debug TC-51 Scoring persistence
# ============================================================

async def debug_tc51():
    print("\n=== DEBUG TC-51 ===")
    players = []
    try:
        _, players, host = await setup_game(draw_time=10, rounds=2, word_count=1, hints=0)
        await host.start_game()

        drawer, guessers, word = await select_first_word(players)
        print(f"Drawer: {drawer.name}")

        await guessers[0].chat(word)
        await guessers[0].wait_for("system_message", timeout=5,
                                   predicate=lambda m: m["data"]["message"] == "Correct guess!")
        await guessers[1].chat(word)

        turn_end = await drawer.wait_for_event("turn_end", timeout=5)
        points = turn_end["data"]["points_awarded"]
        print(f"Points: {points}")

        leaderboard = await drawer.wait_for("leaderboard", timeout=5)
        rows = leaderboard["data"]["players"]
        by_pid = {row["pid"]: row["points"] for row in rows}
        old_score = by_pid[guessers[0].pid]
        print(f"Old score for guesser0: {old_score}")

        await asyncio.sleep(8)
        print("Slept 8 seconds, waiting for next turn...")

        # Next turn - identify_drawer returns (drawer, guessers)
        result = await identify_drawer(players)
        next_drawer = result[0]
        next_guessers = result[1]
        print(f"Next drawer: {next_drawer.name}")

        # Wait for leaderboard after next turn starts
        try:
            persisted = await drawer.wait_for("leaderboard", timeout=5)
            print(f"Persisted leaderboard: {persisted['data']}")
        except asyncio.TimeoutError:
            print("TIMEOUT: No leaderboard in 5 seconds after next turn")

    except Exception:
        traceback.print_exc()
    finally:
        for player in players:
            await player.close()


# ============================================================
# Debug TC-55 GAME_END
# ============================================================

async def debug_tc55():
    print("\n=== DEBUG TC-55 ===")
    players = []
    try:
        _, players, host = await setup_game(draw_time=2, rounds=1, word_count=1, hints=0)
        await host.start_game()

        completed_turns = 0
        last_drawer = None

        while completed_turns < 3:
            drawer, guessers = await identify_drawer(players)
            print(f"Turn {completed_turns+1} drawer: {drawer.name}")

            message = await drawer.wait_for("word_options", timeout=10)
            options = message["data"]["options"]
            word, word_id = options[0]["word"], options[0]["word_id"]

            await drawer.select_word(word_id)
            await drawer.wait_for_event("word_selected", timeout=5)

            await guessers[0].chat(word)
            await guessers[0].wait_for("system_message", timeout=5,
                                       predicate=lambda m: m["data"]["message"] == "Correct guess!")
            await guessers[1].chat(word)

            turn_end = await drawer.wait_for_event("turn_end", timeout=5)
            assert turn_end["data"]["points_awarded"]

            completed_turns += 1
            last_drawer = drawer
            print(f"Completed turn {completed_turns}/3")

            if completed_turns < 3:
                await asyncio.sleep(8)

        print("Waiting for GAME_END...")
        try:
            game_end = await last_drawer.wait_for_state("GAME_END", timeout=10)
            print(f"GAME_END: {game_end['data']}")
        except asyncio.TimeoutError:
            print("TIMEOUT: No GAME_END in 10 seconds")
            print(f"last_drawer messages: {last_drawer.messages}")

        print("Waiting for final leaderboard...")
        try:
            leaderboard = await last_drawer.wait_for("leaderboard", timeout=5)
            print(f"Final leaderboard: {leaderboard['data']}")
        except asyncio.TimeoutError:
            print("TIMEOUT: No final leaderboard in 5 seconds")

        print("Waiting for LOBBY (8 seconds)...")
        await asyncio.sleep(8)
        try:
            lobby = await last_drawer.wait_for_state("LOBBY", timeout=5)
            print(f"LOBBY state: {lobby['data']}")
        except asyncio.TimeoutError:
            print("TIMEOUT: No LOBBY state in 5 seconds")
            print(f"last_drawer messages: {last_drawer.messages}")

    except Exception:
        traceback.print_exc()
    finally:
        for player in players:
            await player.close()


async def main():
    print("=" * 70)
    print("Debugging failing tests")
    print("=" * 70)

    await debug_tc40()
    await debug_tc44()
    await debug_tc45()
    await debug_tc51()
    await debug_tc55()


if __name__ == "__main__":
    asyncio.run(main())
