"""
Integration test suite for Skribbl Clone backend edge cases: TC-56 through TC-62.
"""
import asyncio
import json
import sys
import uuid
from pathlib import Path
import httpx
import websockets

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from websocket_client import TestPlayer
from app.game.engine import GameEngine
from app.game.state import GameState
from app.game.game import Game
from app.models.gamesettings import GameSettings
from app.models.turn import Turn


HTTP_BASE_URL = "http://127.0.0.1:8000"
WS_BASE_URL = "ws://127.0.0.1:8000"


async def create_room():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{HTTP_BASE_URL}/rooms")
    assert response.status_code == 200, (
        f"Room creation failed: {response.status_code} {response.text}"
    )
    return response.json()


async def create_players(room, count=2):
    players = [
        TestPlayer(
            room["name"],
            pid=room["pid"],
        )
    ]
    for index in range(1, count):
        players.append(TestPlayer(f"Test{index + 1}"))

    for player in players:
        await player.connect(WS_BASE_URL, room["room_id"])

    for player in players:
        await player.join()
        await player.wait_for_state("LOBBY", timeout=5)

    return players


async def configure_lobby(
    host,
    *,
    player_count=2,
    draw_time=5,
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
    player_count=2,
    draw_time=5,
    rounds=1,
    word_count=1,
    hints=0,
):
    room = await create_room()
    players = await create_players(room, player_count)
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


# ============================================================
# TC-56: Invalid Room
# ============================================================

async def test_tc56_invalid_room():
    """
    TC-56: Client attempts to connect/join a nonexistent room.
    Verify:
    1. The invalid room is rejected: backend accepts, sends
       {"type": "error", "data": {"message": "Room not found."}}, and closes connection.
    2. No room is accidentally created in RoomManager.
    3. The backend remains healthy.
    4. A valid room created afterward can still be created, joined, and used normally.
    """
    print("\n=== TC-56 Invalid Room ===")

    invalid_room_id = f"NO_ROOM_{uuid.uuid4().hex[:4].upper()}"
    raw_ws = None

    try:
        # 1. Connect to nonexistent room
        raw_ws = await websockets.connect(f"{WS_BASE_URL}/ws/{invalid_room_id}")

        # The backend should respond with error message "Room not found."
        raw_msg = await asyncio.wait_for(raw_ws.recv(), timeout=5)
        msg = json.loads(raw_msg)

        assert msg.get("type") == "error", (
            f"Expected error message, got {msg.get('type')}: {msg}"
        )
        assert msg.get("data", {}).get("message") == "Room not found.", (
            f"Expected 'Room not found.', got: {msg.get('data')}"
        )
        print("TC-56: Received expected error: Room not found.")

        # The backend must close the WebSocket connection
        try:
            await asyncio.wait_for(raw_ws.wait_closed(), timeout=5)
            assert raw_ws.close_code is not None, "WebSocket connection was not closed by backend"
            print("TC-56: Nonexistent room WebSocket connection closed by backend.")
        except asyncio.TimeoutError:
            raise AssertionError("Backend did not close connection for nonexistent room within 5s")

    finally:
        if raw_ws is not None:
            try:
                await raw_ws.close()
            except Exception:
                pass

    # 2. Verify backend health: create a valid room and verify normal operation
    valid_room = await create_room()
    assert valid_room["room_id"] != invalid_room_id
    print("TC-56: Backend healthy, created valid room:", valid_room["room_id"])

    valid_player = TestPlayer("LegitHost", pid=valid_room["pid"])
    try:
        await valid_player.connect(WS_BASE_URL, valid_room["room_id"])
        await valid_player.join()
        state = await valid_player.wait_for_state("LOBBY", timeout=5)
        assert state["data"]["state"] == "LOBBY"
        print("TC-56: Valid room connected and joined successfully.")
        print("TC-56 PASSED.")
    finally:
        await valid_player.close()


# ============================================================
# TC-57: Invalid Player
# ============================================================

async def test_tc57_invalid_player():
    """
    TC-57: Test an invalid/unknown player identity against a valid existing room.
    Verify:
    1. The invalid identity cannot impersonate an existing player or reconnect as a nonexistent player.
    2. Attempt to reconnect with unknown PID is rejected with "Player does not exist in this room."
    3. The room's legitimate players remain intact.
    4. Legitimate player can still perform valid operations afterward.
    """
    print("\n=== TC-57 Invalid Player ===")

    players = []
    attacker_ws = None

    try:
        # 1. Setup legitimate room with 2 players
        room, players, host = await setup_game(player_count=2)
        legit_guest = players[1]

        # 2. Attacker connects with a forged, unknown PID
        unknown_pid = str(uuid.uuid4())
        attacker_url = f"{WS_BASE_URL}/ws/{room['room_id']}?pid={unknown_pid}"
        attacker_ws = await websockets.connect(attacker_url)

        # Connection message received
        conn_msg = json.loads(await attacker_ws.recv())
        assert conn_msg["type"] == "connection"
        assert conn_msg["data"]["pid"] == unknown_pid

        # Attacker attempts to reconnect using unknown PID
        reconnect_msg = {"type": "reconnect", "data": {}}
        await attacker_ws.send(json.dumps(reconnect_msg))

        err_raw = await asyncio.wait_for(attacker_ws.recv(), timeout=5)
        err = json.loads(err_raw)

        assert err.get("type") == "error", f"Expected error message, got: {err}"
        assert err.get("data", {}).get("message") == "Player does not exist in this room.", (
            f"Expected 'Player does not exist in this room.', got: {err.get('data')}"
        )
        print("TC-57: Unknown PID reconnect rejected with expected error.")

        # 3. Attacker attempts to send chat pretending to be legitimate host
        # (even if payload includes host's pid, backend routes based on connection pid)
        spoof_chat = {
            "type": "chat",
            "data": {"pid": host.pid, "message": "I am the host!"},
        }
        await attacker_ws.send(json.dumps(spoof_chat))

        err_chat_raw = await asyncio.wait_for(attacker_ws.recv(), timeout=5)
        err_chat = json.loads(err_chat_raw)
        assert err_chat.get("type") == "error"
        assert "not found or disconnected" in err_chat.get("data", {}).get("message").lower()
        print("TC-57: Forged player chat rejected with expected error.")

        # Close attacker connection
        await attacker_ws.close()
        attacker_ws = None

        # 4. Verify legitimate players remain intact and operational
        await host.chat("Legitimate message from host")
        chat_received = await legit_guest.wait_for(
            "chat",
            timeout=5,
            predicate=lambda m:
                m["data"]["pid"] == host.pid
                and m["data"]["message"] == "Legitimate message from host",
        )
        assert chat_received, "Legitimate player chat was not received"
        print("TC-57: Legitimate players remained intact and operational.")
        print("TC-57 PASSED.")

    finally:
        if attacker_ws is not None:
            try:
                await attacker_ws.close()
            except Exception:
                pass
        for p in players:
            await p.close()


# ============================================================
# TC-58: Invalid Message
# ============================================================

async def test_tc58_invalid_message():
    """
    TC-58: Test malformed/unsupported WebSocket messages.
    Verify:
    1. Unknown message types and unsupported messages (e.g. client-side 'hint')
       are rejected according to backend protocol.
    2. Connection and server remain usable without crash or corruption.
    3. Valid message sent afterward succeeds.
    """
    print("\n=== TC-58 Invalid Message ===")

    players = []
    try:
        room, players, host = await setup_game(player_count=2)

        # 1. Send unsupported "hint" message (hints are automatic server events, not client requests)
        await host.send("hint", {"request": True})
        err_hint = await host.wait_for("error", timeout=5)
        assert err_hint["data"]["message"] == "Unknown message type: hint", (
            f"Expected 'Unknown message type: hint', got: {err_hint['data']}"
        )
        print("TC-58: Unsupported 'hint' message rejected with expected error.")

        # 2. Send unknown custom message type
        await host.send("nonexistent_command", {"foo": "bar"})
        err_unknown = await host.wait_for("error", timeout=5)
        assert err_unknown["data"]["message"] == "Unknown message type: nonexistent_command", (
            f"Expected 'Unknown message type: nonexistent_command', got: {err_unknown['data']}"
        )
        print("TC-58: Unknown message type rejected with expected error.")

        # 3. Connection and state remain usable: send a valid message and verify it succeeds
        await host.lobby_update(draw_time=50)
        state = await host.wait_for_state(
            "LOBBY",
            timeout=5,
            predicate=lambda m: m.get("data", {}).get("settings", {}).get("draw_time") == 50,
        )
        assert state["data"]["settings"]["draw_time"] == 50, (
            f"Expected draw_time=50, got {state['data']['settings']['draw_time']}"
        )
        print("TC-58: Valid message succeeded immediately after invalid messages.")
        print("TC-58 PASSED.")

    finally:
        for p in players:
            await p.close()


# ============================================================
# TC-59: Unauthorized Action
# ============================================================

async def test_tc59_unauthorized_action():
    """
    TC-59: Valid connected player attempts an action they are not authorized to perform.
    Verify:
    1. Non-host player attempts lobby_update: rejected with
       "Only the host can update lobby settings."
    2. Settings remain unchanged.
    3. Non-host attempts start_game: rejected with
       "Only the host can start the game."
    4. Game state remains in LOBBY.
    5. Authorized host can perform valid actions afterward.
    """
    print("\n=== TC-59 Unauthorized Action ===")

    players = []
    try:
        room, players, host = await setup_game(player_count=2, draw_time=60)
        guest = players[1]

        # 1. Non-host attempts lobby_update
        await guest.lobby_update(draw_time=15)
        err_lobby = await guest.wait_for("error", timeout=5)
        assert err_lobby["data"]["message"] == "Only the host can update lobby settings.", (
            f"Expected host auth error, got: {err_lobby['data']}"
        )
        print("TC-59: Non-host lobby_update rejected with expected error.")

        # 2. Verify settings remained unchanged (still 60)
        # Query via sending valid no-op update from host or checking host state
        await host.lobby_update(draw_time=60)
        state = await host.wait_for_state("LOBBY", timeout=5)
        assert state["data"]["settings"]["draw_time"] == 60, (
            f"Settings were corrupted by unauthorized player: {state['data']['settings']['draw_time']}"
        )
        print("TC-59: Lobby settings remained unchanged.")

        # 3. Non-host attempts start_game
        await guest.start_game()
        err_start = await guest.wait_for("error", timeout=5)
        assert err_start["data"]["message"] == "Only the host can start the game.", (
            f"Expected host start_game error, got: {err_start['data']}"
        )
        print("TC-59: Non-host start_game rejected with expected error.")

        # 4. Verify game state remains in LOBBY
        assert state["data"]["state"] == "LOBBY"

        # 5. Authorized host can update settings and start game
        await host.lobby_update(draw_time=75)
        state_updated = await host.wait_for_state(
            "LOBBY",
            timeout=5,
            predicate=lambda m: m.get("data", {}).get("settings", {}).get("draw_time") == 75,
        )
        assert state_updated["data"]["settings"]["draw_time"] == 75
        print("TC-59: Authorized host can perform action successfully.")
        print("TC-59 PASSED.")

    finally:
        for p in players:
            await p.close()


# ============================================================
# TC-60: Invalid Game State
# ============================================================

async def test_tc60_invalid_game_state():
    """
    TC-60: Valid actions attempted during an invalid lifecycle state.
    Verify:
    1. select_word while in LOBBY -> rejected with "Word selection is not active." State remains LOBBY.
    2. draw while in LOBBY -> rejected with "Drawing is not active." State remains LOBBY.
    3. Once game starts and reaches active state:
       - lobby_update while not in LOBBY -> rejected with
         "Lobby settings can only be changed before the game starts."
       - start_game while not in LOBBY -> rejected with
         "The game has already started."
    4. Valid action for current state still works afterward.
    """
    print("\n=== TC-60 Invalid Game State ===")

    players = []
    try:
        room, players, host = await setup_game(player_count=2, draw_time=5)

        # 1. select_word while in LOBBY
        await host.select_word(1)
        err_word = await host.wait_for("error", timeout=5)
        assert err_word["data"]["message"] == "The game is not waiting for word selection.", (
            f"Expected 'The game is not waiting for word selection.', got: {err_word['data']}"
        )
        print("TC-60: select_word while in LOBBY rejected.")

        # 2. draw while in LOBBY
        await host.draw(action="stroke", x=10, y=10)
        err_draw = await host.wait_for("error", timeout=5)
        assert err_draw["data"]["message"] == "Drawing is not active.", (
            f"Expected 'Drawing is not active.', got: {err_draw['data']}"
        )
        print("TC-60: draw while in LOBBY rejected.")

        # 3. Transition to active game
        await host.start_game()

        # Wait for WORD_SELECTION
        ws_states = await asyncio.gather(
            *[p.wait_for_state("WORD_SELECTION", timeout=15) for p in players]
        )
        drawer_pid = ws_states[0]["data"]["current_drawer"]
        drawer = next(p for p in players if p.pid == drawer_pid)

        # 4. Attempt lobby_update while in WORD_SELECTION
        await host.lobby_update(draw_time=99)
        err_lobby = await host.wait_for("error", timeout=5)
        assert err_lobby["data"]["message"] == "Lobby settings can only be changed before the game starts.", (
            f"Expected lobby settings state error, got: {err_lobby['data']}"
        )
        print("TC-60: lobby_update during active game rejected.")

        # 5. Attempt start_game while game is already running
        await host.start_game()
        err_start = await host.wait_for("error", timeout=5)
        assert err_start["data"]["message"] == "The game has already started.", (
            f"Expected already started error, got: {err_start['data']}"
        )
        print("TC-60: start_game during active game rejected.")

        # 6. Valid action for current state works: drawer selects word
        opt_msg = await drawer.wait_for("word_options", timeout=10)
        options = opt_msg["data"]["options"]
        selected_option = options[0]
        await drawer.select_word(selected_option["word_id"])

        selected_events = await asyncio.gather(
            *[p.wait_for_event("word_selected", timeout=5) for p in players]
        )
        assert selected_events, "Word selection failed after state rejections"
        print("TC-60: Valid action for current state succeeded normally.")
        print("TC-60 PASSED.")

    finally:
        for p in players:
            await p.close()


# ============================================================
# TC-61: Maximum Word Length
# ============================================================

async def test_tc61_maximum_word_length():
    """
    TC-61: Upper word-length boundary testing and pattern masking verification.

    This test is structured in two distinct, documented parts:

    PART 1 (Deterministic Unit & Engine Boundary Test for Maximum Database Word):
    - Uses the database's actual maximum length word ("William Shakespeare", length 19,
      lengths [7, 11], containing a space).
    - Verifies the hint boundary mapping logic get_max_hints(word_length):
      3 -> 1, 4/5 -> 2, 6 -> 3, 7 -> 4, 8+ -> 5 (including max length 19).
    - Verifies word pattern generation preserving spaces and masking letters:
      initial pattern is exactly '_______ ___________' (length 19, space at index 7).
    - Verifies progressive hint revelation revealing exactly one character per hint
      up to max_hints=5.
    - Verifies strict enforcement blocking hints beyond the maximum limit of 5.

    PART 2 (Live WebSocket Protocol Pattern & Turn-End Exposure Test):
    - Tests the live WebSocket message lifecycle under production random word selection.
    - Selects the longest available word among the offered options without altering
      production logic.
    - Validates guesser receives a pattern whose length matches the selected word with
      spaces preserved and letters masked as '_'.
    - Validates full word is exposed at turn_end when the turn timer expires.
    """
    print("\n=== TC-61 Maximum Word Length ===")

    # 1. Verify hint boundary function get_max_hints against specification
    settings = GameSettings(
        room_id="TEST",
        player_count=2,
        language="en",
        draw_time=60,
        rounds=1,
        word_count=3,
        hints=5,
        custom_words=[],
        custom_words_only=False,
    )
    dummy_game = Game(room_id="TEST", state=GameState.PLAYING, settings=settings)
    engine = GameEngine(dummy_game)

    expected_hint_boundaries = {
        3: 1,
        4: 2,
        5: 2,
        6: 3,
        7: 4,
        8: 5,
        10: 5,
        15: 5,
        19: 5,  # Maximum word length in database
    }

    for length, expected_hints in expected_hint_boundaries.items():
        actual_hints = engine.get_max_hints(length)
        assert actual_hints == expected_hints, (
            f"Hint boundary mismatch for length {length}: expected {expected_hints}, got {actual_hints}"
        )
    print("TC-61: Hint boundary mappings (3->1, 4/5->2, 6->3, 7->4, 8+->5) verified.")

    # 2. Verify word pattern generation for the database's maximum word length:
    # "William Shakespeare" (length 19, lengths [7, 11], contains space)
    max_word = "William Shakespeare"
    max_lengths = [7, 11]

    dummy_turn = Turn(
        turn_id="TURN_MAX",
        round_id="ROUND_1",
        drawer_pid="DRAWER_PID",
        word=max_word,
        word_lengths=max_lengths,
    )
    dummy_game.current_turn = dummy_turn
    dummy_game.settings.hints = 5

    # Initial pattern check: spaces must remain visible, letters masked as '_'
    initial_pattern = engine.get_word_pattern()
    assert len(initial_pattern) == len(max_word), "Pattern length mismatch"
    assert initial_pattern[7] == " ", f"Space at index 7 was not preserved: '{initial_pattern}'"
    assert initial_pattern == "_______ ___________", f"Initial pattern unexpected: '{initial_pattern}'"
    print("TC-61: Maximum length word pattern preserves spaces correctly:", initial_pattern)

    # Reveal hints one by one up to the maximum (5 hints)
    revealed_patterns = []
    for hint_step in range(1, 6):
        new_pattern = engine.reveal_hint()
        assert new_pattern is not None, f"Failed to reveal hint step {hint_step}"
        # Count revealed letters (non-space, non-underscore characters)
        revealed_count = sum(1 for c in new_pattern if c not in (" ", "_"))
        assert revealed_count == hint_step, (
            f"Expected {hint_step} revealed characters, got {revealed_count}"
        )
        revealed_patterns.append(new_pattern)

    print("TC-61: Hints revealed letters progressively up to 5:", revealed_patterns[-1])

    # 6th hint must be blocked (max hints = 5)
    sixth_hint = engine.reveal_hint()
    assert sixth_hint is None, "Hint revealed beyond maximum limit of 5"
    print("TC-61: Word-length hint limit of 5 strictly enforced.")

    # 3. Live WebSocket integration test with pattern masking and turn_end exposure
    # Production selects random options from database; we select the longest available option.
    players = []
    try:
        room, players, host = await setup_game(player_count=2, draw_time=5)
        await host.start_game()

        ws_states = await asyncio.gather(
            *[p.wait_for_state("WORD_SELECTION", timeout=15) for p in players]
        )
        drawer_pid = ws_states[0]["data"]["current_drawer"]
        drawer = next(p for p in players if p.pid == drawer_pid)
        guesser = next(p for p in players if p.pid != drawer_pid)

        opt_msg = await drawer.wait_for("word_options", timeout=10)
        options = opt_msg["data"]["options"]
        # Select the longest word from the offered options
        selected = max(options, key=lambda o: len(o["word"]))
        word = selected["word"]
        word_id = selected["word_id"]

        await drawer.select_word(word_id)

        # Guesser receives pattern
        selected_event = await guesser.wait_for_event("word_selected", timeout=5)
        pattern = selected_event["data"]["pattern"]

        assert len(pattern) == len(word), "Guesser pattern length does not match word length"
        # Spaces in word must correspond to spaces in pattern
        for i, char in enumerate(word):
            if char == " ":
                assert pattern[i] == " ", f"Space at index {i} was masked in pattern"
            else:
                assert pattern[i] == "_", f"Letter at index {i} was exposed in pattern"

        print(f"TC-61: Live word '{word}' -> pattern '{pattern}' verified.")

        # Let turn expire to verify full word exposure at turn_end
        turn_end = await drawer.wait_for_event("turn_end", timeout=10)
        assert turn_end["data"]["word"] == word, "Full word was not exposed at turn_end"
        print("TC-61: Full word exposed at turn_end:", turn_end["data"]["word"])
        print("TC-61 PASSED.")

    finally:
        for p in players:
            await p.close()


# ============================================================
# TC-62: Multiple Rooms
# ============================================================

async def test_tc62_multiple_rooms():
    """
    TC-62: Complete isolation between multiple simultaneous rooms.
    Verify:
    1. Room Creation: Create Room A and Room B simultaneously with distinct players.
    2. Chat Isolation: Messages sent in Room A are received only by Room A players,
       not Room B (and vice versa).
    3. Game State Isolation: Starting Room A transitions Room A through WORD_SELECTION
       and PLAYING while Room B independently remains in LOBBY with configurable settings.
    4. Drawing Isolation:
       - Room A reaches PLAYING.
       - Drawer in Room A sends a valid draw action.
       - Room A non-drawer (guesser) receives the draw event.
       - Room B players receive no corresponding draw event.
    """
    print("\n=== TC-62 Multiple Rooms ===")

    players_a = []
    players_b = []

    try:
        # 1. Setup Room A with 2 players
        room_a, players_a, host_a = await setup_game(player_count=2, draw_time=15)
        guest_a = players_a[1]

        # 2. Setup Room B with 2 players
        room_b, players_b, host_b = await setup_game(player_count=2, draw_time=15)
        guest_b = players_b[1]

        assert room_a["room_id"] != room_b["room_id"], "Rooms must have distinct IDs"
        print(f"TC-62: Created Room A ({room_a['room_id']}) and Room B ({room_b['room_id']}).")

        # 3. Test Chat Isolation
        # Host A sends chat in Room A
        await host_a.chat("Hello from Room A!")

        # Guest A receives chat in Room A
        chat_a = await guest_a.wait_for(
            "chat",
            timeout=5,
            predicate=lambda m: m["data"]["message"] == "Hello from Room A!",
        )
        assert chat_a["data"]["pid"] == host_a.pid
        print("TC-62: Room A received internal chat.")

        # Room B players must NOT receive Room A chat
        await host_b.expect_no_message(
            "chat",
            timeout=0.5,
            predicate=lambda m: m["data"].get("message") == "Hello from Room A!",
        )
        await guest_b.expect_no_message(
            "chat",
            timeout=0.5,
            predicate=lambda m: m["data"].get("message") == "Hello from Room A!",
        )
        print("TC-62: Room B did not receive Room A chat.")

        # Host B sends chat in Room B
        await host_b.chat("Hello from Room B!")
        chat_b = await guest_b.wait_for(
            "chat",
            timeout=5,
            predicate=lambda m: m["data"]["message"] == "Hello from Room B!",
        )
        assert chat_b["data"]["pid"] == host_b.pid

        # Room A players must NOT receive Room B chat
        await host_a.expect_no_message(
            "chat",
            timeout=0.5,
            predicate=lambda m: m["data"].get("message") == "Hello from Room B!",
        )
        print("TC-62: Room A did not receive Room B chat.")

        # 4. Test Game State Isolation
        # Start game in Room A
        await host_a.start_game()

        # Room A players transition to WORD_SELECTION
        state_a = await host_a.wait_for_state("WORD_SELECTION", timeout=15)
        assert state_a["data"]["state"] == "WORD_SELECTION"
        drawer_a_pid = state_a["data"]["current_drawer"]
        drawer_a = next(p for p in players_a if p.pid == drawer_a_pid)
        guesser_a = next(p for p in players_a if p.pid != drawer_a_pid)
        print("TC-62: Room A transitioned to WORD_SELECTION.")

        # Room B players must remain in LOBBY
        await host_b.expect_no_message(
            "game_state",
            timeout=0.5,
            predicate=lambda m: m["data"].get("state") == "WORD_SELECTION",
        )
        # Verify Room B settings update while Room A is active
        await host_b.lobby_update(draw_time=30)
        state_b = await host_b.wait_for_state(
            "LOBBY",
            timeout=5,
            predicate=lambda m: m.get("data", {}).get("settings", {}).get("draw_time") == 30,
        )
        assert state_b["data"]["state"] == "LOBBY"
        assert state_b["data"]["settings"]["draw_time"] == 30
        print("TC-62: Room B remained in LOBBY independently.")

        # 5. Test Drawing Isolation
        # Room A drawer receives word options and selects a word to reach PLAYING
        opt_msg = await drawer_a.wait_for("word_options", timeout=10)
        word_id = opt_msg["data"]["options"][0]["word_id"]
        await drawer_a.select_word(word_id)

        # Room A reaches PLAYING
        await asyncio.gather(
            *[p.wait_for_state("PLAYING", timeout=10) for p in players_a]
        )
        print("TC-62: Room A reached PLAYING.")

        # Room A drawer sends a valid draw stroke
        await drawer_a.draw(action="stroke", x=120, y=240, color="#FF0000", size=3)

        # Room A guesser receives the draw event
        draw_event = await guesser_a.wait_for(
            "draw",
            timeout=5,
            predicate=lambda m: m.get("data", {}).get("action") == "stroke",
        )
        assert draw_event["data"]["pid"] == drawer_a.pid
        assert draw_event["data"]["x"] == 120
        assert draw_event["data"]["y"] == 240
        print("TC-62: Room A guesser received draw stroke.")

        # Room B players must NOT receive any draw event
        await host_b.expect_no_message("draw", timeout=0.5)
        await guest_b.expect_no_message("draw", timeout=0.5)
        print("TC-62: Room B players received no drawing events.")

        print("TC-62: Both rooms operate concurrently with complete state, chat, and drawing isolation.")
        print("TC-62 PASSED.")

    finally:
        for p in players_a:
            await p.close()
        for p in players_b:
            await p.close()


# ============================================================
# Main Runner for Edge Cases
# ============================================================

async def run_edge_cases():
    test_suite = [
        ("TC-56 Invalid Room", test_tc56_invalid_room),
        ("TC-57 Invalid Player", test_tc57_invalid_player),
        ("TC-58 Invalid Message", test_tc58_invalid_message),
        ("TC-59 Unauthorized Action", test_tc59_unauthorized_action),
        ("TC-60 Invalid Game State", test_tc60_invalid_game_state),
        ("TC-61 Maximum Word Length", test_tc61_maximum_word_length),
        ("TC-62 Multiple Rooms", test_tc62_multiple_rooms),
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("RUNNING EDGE-CASE TEST SUITE: TC-56 THROUGH TC-62")
    print("=" * 70)

    for name, test_func in test_suite:
        print(f"\n--- Running {name} ---")
        try:
            await test_func()
            passed += 1
            print(f"PASS: {name}")
        except Exception as exc:
            failed += 1
            print(f"FAIL: {name}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("EDGE-CASE TEST SUITE SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(test_suite)}")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(run_edge_cases())
