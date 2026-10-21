# 🎨 Skribbl.io Clone – Real-Time Multiplayer Drawing & Guessing Game

A web-based multiplayer game where one player draws a secret word and everyone else races to guess it. Players join rooms with a code, chat, earn points for fast guesses, and compete on a live leaderboard.

Traditional drawing games need everyone in the same room. This project lets people play together online from anywhere, using only a web browser. No installation is needed. Players just share a room code.

| Item | Details |
|------|---------|
| **Project Name** | Skribbl.io Clone |
| **Type** | Real-time multiplayer web game |
| **Purpose** | Let users draw and guess words together in real time |
| **Users** | Players and Hosts |
| **Design Tool** | Figma (low-fidelity wireframes) |
| **Dev Tools** | Visual Studio Code, Git, GitHub, Postman |

### Aim
To build a user-friendly multiplayer drawing and guessing game inspired by Skribbl.io.

### Objectives
- Build a simple, easy-to-use interface
- Implement the main game screens (home, lobby, game, results)
- Support word selection, drawing, guessing, and chat
- Show scores and rankings on a leaderboard
- Test every implemented feature

### Key Terms

| Term | Meaning |
|------|---------|
| **Host** | The player who creates the room and controls its settings |
| **Player** | Anyone taking part in the game (draws, guesses, chats) |
| **Drawer** | The player currently drawing the secret word |
| **Round** | One complete cycle where every player gets a turn to draw |
| **Turn** | One player's drawing session |
| **Leaderboard** | Ranking of players by score |

---

## 🎮 How the Game Works

1. **Enter the game** – Choose a username and an avatar.
2. **Create or join a room** – The host creates a room and shares the room code. Friends join using that code.
3. **Wait in the lobby** – Everyone sees who has joined and can chat. The host starts the game.
4. **Pick a word** – The drawer chooses 1 of 3 random words (auto-picked if they take too long).
5. **Draw and guess** – The drawer sketches the word. Everyone else types guesses in the chat. Letter hints appear over time.
6. **Score points** – The faster you guess, the more points you earn.
7. **Next turn** – The next player becomes the drawer. This repeats for all rounds.
8. **Winner** – A final leaderboard shows the winner. Play again or return to the lobby.

---

## ✨ Key Features

### 🏠 Home Page
- Enter a username and choose an avatar
- Create a room, or join one using a room code

### 🚪 Room Management
- Auto-generated unique room code
- Host configures **number of players**, **number of rounds**, and the **drawing timer**

### 🛋 Lobby
- Live list of players and the host
- Room settings display
- Lobby chat
- Start-game button (host only)

### 🔤 Word Selection
- Drawer picks from 3 random words
- Automatic word selection after a 15-second timeout

### 🖌 Drawing Canvas (HTML5 Canvas)
- Brush with multiple colours
- Adjustable brush size
- Eraser and clear-canvas tools
- **Real-time stroke synchronisation** to all players

### 🎯 Gameplay
- Automatic drawer assignment each turn
- Guess validation
- Progressive **hints** (letters revealed over time)
- Turn timer, turn switching, and round completion

### 💬 Chat and Scoring
- Real-time chat
- Correct guesses are hidden from players who are still guessing
- Speed-based scoring with live updates
- Leaderboard and winner announcement

### 🔁 Game Management
- Final results screen
- Replay option
- Host controls
- Return to lobby

### 🔌 Reliability Features
- **Late joining:** players can join a game in progress as guessers
- **Reconnection:** a dropped player can rejoin with the same player ID and get their state back
- **30-second grace period** before a disconnected player is removed
- **Host transfer** if the host permanently leaves

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, JavaScript (ES6+), HTML5, CSS3, HTML5 Canvas API |
| **Backend** | Python, FastAPI, Uvicorn (ASGI server) |
| **Real-time** | WebSockets |
| **Database** | SQLite |
| **Communication** | WebSockets + HTTPS (REST) |
| **Design** | Figma |
| **Testing** | Postman, automated Python test scripts |
| **Tools** | VS Code, Git, GitHub |

### Software Requirements

| Category | Item | Specification |
|----------|------|---------------|
| Software | Operating System | Windows 10/11 (macOS/Linux also work) |
| Software | Languages | JavaScript, Python |
| Software | Frameworks | React, FastAPI |
| Software | IDE | VS Code |
| Software | Version Control | Git and GitHub |
| Hardware | Network | Internet connection |

---

## 🏗 System Architecture

```
┌──────────────────────┐      HTTPS (REST)       ┌──────────────────────┐
│   React Frontend     │ ──────────────────────► │   FastAPI Backend    │
│  (Canvas, Lobby,     │                         │  (Room APIs, Game    │
│   Chat, Leaderboard) │ ◄─────────────────────► │   Logic, Validation) │
└──────────────────────┘     WebSockets (WS)     └──────────┬───────────┘
                                                            │
                                                            ▼
                                                  ┌──────────────────┐
                                                  │     Database     │
                                                  │ (Rooms, Words,   │
                                                  │  Scores)         │
                                                  └──────────────────┘
```

- **REST (HTTPS):** checking backend status, creating rooms, joining and validating rooms
- **WebSockets:** drawing strokes, chat, guesses, timers, scores, turn changes
- **Backend:** keeps live room state in memory and uses the database for persistent data (word bank, results)

### Main Modules

| Module | What it does |
|--------|--------------|
| **Room Management** | Creates rooms, assigns the host, manages joining and capacity |
| **Game Management** | Controls rounds, turns, word selection, and state changes |
| **Drawing and Guessing** | Broadcasts drawings, processes guesses, protects the secret word |
| **Scoring and Leaderboard** | Calculates points, awards speed bonuses, updates rankings |
| **Connection Management** | Handles disconnects, reconnects, and host migration |
| **Security and Validation** | Rejects unauthorised actions, invalid messages, and invalid game states |

---

## 🔄 Game Flow and State Machine

```
Home Page → Create/Join Room → Lobby → Host Starts Game
      → Drawer Picks Word (1 of 3) → Drawing + Guessing (timer, hints)
      → Turn Ends → Scores Updated → Next Drawer
      → All Rounds Complete → Final Leaderboard & Winner
      → Replay / Return to Lobby
```

The backend game state machine moves through these states:

```
LOBBY → ROUND_START → TURN_START → WORD_SELECTION → PLAYING → TURN_END → ROUND_END → GAME_END
```

- After `TURN_END`, the game goes to the next drawer, or to `ROUND_END` once everyone has drawn.
- After `ROUND_END`, it starts a new round, or goes to `GAME_END` when all rounds are done.
- If the drawer disconnects during word selection or play, the turn ends.
- If fewer than two players remain connected, the game ends.

### Timers

| Timer | Duration |
|-------|----------|
| Round-start countdown | 3 seconds |
| Word-selection countdown | 15 seconds |
| Drawing/guessing timer | Configurable (default 80 seconds) |
| Leaderboard display | 7 seconds |

Timer updates are broadcast to all clients every second.

---

## 💻 Frontend Details

### Screens
1. **Home Page** – username, avatar, create/join
2. **Lobby** – players, settings, chat, start button
3. **Game Screen** – canvas, toolbar, chat panel, player list, timer, word hint
4. **Result Screen** – final leaderboard, winner, replay

### Main Components
- `Canvas` – drawing area with mouse event handling
- `Toolbar` – brush, colour picker, size slider, eraser, clear
- `ChatBox` – messages and guess input
- `PlayerList` – avatars, names, live scores, drawer indicator
- `Timer` and `WordHint`
- `WordSelectModal` – shown only to the drawer
- `Leaderboard`

### Responsibilities
- Capture drawing events and send them over WebSocket
- Render strokes received from other players
- Manage the WebSocket connection and reconnection
- Responsive layout for desktop and laptop screens

---

## ⚙️ Backend and Networking Details

### Responsibilities
- Create and validate rooms; generate unique room codes
- Manage WebSocket connections for each room
- Broadcast drawing data, chat, and game events
- Control game state from lobby to results
- Assign drawers, serve random words, run timers, reveal hints
- Validate guesses and calculate scores
- Validate input and enforce security checks

### Networking Module – What Was Built

| Area | What it does |
|------|--------------|
| **WebSocket communication** | Real-time client-server messaging with unique player IDs and connect/disconnect handling |
| **Message routing** | Server-side routing for every client message type (see reference below) |
| **Player join and rooms** | Name and avatar validation, host assignment, capacity checks, duplicate-connection prevention |
| **Late joining** | Players can join mid-game as guessers without interrupting the current turn, and are added to future turns |
| **Reconnection** | Rejoin with the same player ID; no duplicate player is created; game state is restored |
| **Disconnect and grace period** | 30-second window to reconnect; others are notified; permanent removal after expiry; host transfer if needed |
| **Chat and guess networking** | Integrated with `GameEngine.process_guess()`; messages are classified as normal chat, close guess, wrong guess, or correct guess |
| **Word visibility** | Drawer sees the full word; guessers see a hidden pattern; correct guessers see the full word; everyone sees it when the turn ends |
| **Word selection** | Options sent only to the drawer, with a 15-second timer and auto-select |
| **Real-time drawing** | Strokes from the drawer are relayed to everyone else; only the drawer may send drawing data |
| **Game timers** | Async tasks for countdowns, drawing time, and leaderboard display |
| **Automatic hints** | Hints are spaced across the drawing timer using `GameEngine.reveal_hint()` |
| **Turn and round sync** | Coordinates round start, word selection, drawing, turn end, leaderboard, next turn/round, and game end |
| **Game state sync** | Players, connection status, host, settings, round, turn, drawer, and leaderboard are kept consistent |
| **Lobby updates** | Host-only settings changes with validation (capacity cannot drop below current player count) |
| **Error handling** | Clear errors for invalid room, invalid player, bad word choice, unauthorised actions, wrong game state, bad profile data, non-drawer drawing, and non-host actions |
| **Async runtime** | Background tasks for timers, hints, transitions, and grace periods, with cancellation so old timers never affect later turns |

### Scoring
- Points are awarded for correct guesses.
- Faster guesses earn speed bonuses.
- Scores persist across rounds and update live on the leaderboard.

---

## 🔌 API and WebSocket Reference

### REST Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/rooms/{code}` | Get room details |
| POST | `/api/rooms` | Create a room (returns room code) |
| POST | `/api/rooms/{code}/join` | Join a room |
| WS | `/ws/{room_code}` | Real-time game connection |

### WebSocket Messages: Client → Server

| Message | Purpose |
|---------|---------|
| `join` | Join the room as a player |
| `reconnect` | Rejoin using an existing player ID |
| `chat` | Send a chat message or guess |
| `select_word` | Drawer picks a word |
| `draw` | Drawer sends stroke data |
| `lobby_update` | Host changes room settings |
| `start_game` | Host starts the game |

### WebSocket Messages: Server → Client

| Message | Purpose |
|---------|---------|
| `connection` | Connection confirmed, player ID assigned |
| `game_state` | Full synchronised game state |
| `word_options` | 3 word choices (drawer only) |
| `chat` | Chat or guess result message |
| `system_message` | Announcements (joins, correct guesses, etc.) |
| `timer` | Remaining time, sent every second |
| `leaderboard` | Current scores and rankings |
| `draw` | Stroke data relayed to guessers |
| `player_joined` | A player joined |
| `player_left` | A player left or was removed |
| `error` | An invalid action was attempted |

---

## 🗄 Database Design

| Table | Fields |
|-------|--------|
| **rooms** | `room_code`, `host`, `max_players`, `rounds`, `timer`, `status`, `created_at` |
| **players** | `username`, `avatar`, `room_code`, `score` |
| **words** | `word`, `category` / `difficulty` |
| **game_results** | `room_code`, `final_scores`, `winner`, `played_at` |

### Game Data Used During Play

| Attribute | Type | Description |
|-----------|------|-------------|
| Player Name | String | Identifies a player |
| Selected Word | String | Word chosen for drawing (from a predefined list) |
| Guess | String | Word entered by a player |
| Score | Integer | Points earned (non-negative) |

> This project does not use machine learning, so no ML dataset is needed.

---

## 📁 Project Structure

```
skribbl-clone/
├── frontend/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── services/        # API + WebSocket helpers
│       ├── styles/
│       └── App.jsx
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── websocket/       # connection manager, event handlers
│   │   ├── game/            # game logic, scoring, timers
│   │   ├── models/
│   │   └── database.py
│   └── requirements.txt
├── design/
│   └── low-fidelity/        # Figma wireframes
├── docs/
│   ├── SRS.pdf
│   └── Tech_Stack.pdf
└── README.md

## 🧪 Testing

Testing used a **Postman API collection** and **automated Python test scripts**. The test report documents **65 test cases with a 100% pass rate**.

| Test Category | Coverage | Result |
|---------------|----------|--------|
| REST API and room management | Backend status, room creation, player joining | ✅ PASS |
| Game lifecycle | Game start, turns, rounds, game completion | ✅ PASS |
| Drawing and guessing | Drawing broadcasts, word selection, guesses | ✅ PASS |
| Scoring and leaderboard | Point calculation, speed bonuses, rankings | ✅ PASS |
| Security and edge cases | Invalid actions, unauthorised requests, invalid messages | ✅ PASS |
| Reconnection and recovery | Reconnection, host migration, disconnection handling | ✅ PASS |
| End-to-end | Complete multiplayer match flow | ✅ PASS |

### Functional Test Cases

| # | Test Case | Expected Result | Status |
|---|-----------|-----------------|--------|
| 1 | Create a game room | Room is created successfully | ✅ PASS |
| 2 | Join an existing room | Player joins successfully | ✅ PASS |
| 3 | Select a word | Valid word is accepted | ✅ PASS |
| 4 | Draw on the canvas | Drawing is broadcast to other players | ✅ PASS |
| 5 | Submit a correct guess | Correct guess is recognised | ✅ PASS |
| 6 | Submit an incorrect guess | Incorrect guess is handled correctly | ✅ PASS |
| 7 | Update player scores | Scores are calculated and updated | ✅ PASS |
| 8 | Disconnect and reconnect | Player state is recovered within the grace period | ✅ PASS |
| 9 | Send an unauthorised action | Action is rejected | ✅ PASS |
| 10 | Complete a game | Final leaderboard is displayed | ✅ PASS |

The automated tests also confirm that drawings reach all players, secret words stay hidden from guessers, scores persist across rounds, and separate rooms stay isolated.

---

## 📊 Project Status

### Backend
- [x] FastAPI project setup
- [x] Room creation and joining APIs
- [x] WebSocket connection manager
- [x] Real-time drawing synchronisation
- [x] Game state management (turns, rounds, timers)
- [x] Word bank and random word selection
- [x] Guess validation and scoring logic
- [x] Hint reveal system
- [x] Reconnection, late joining, and host migration
- [x] Input validation and security checks

### Frontend
- [x] Home page (username, avatar, create/join)
- [x] Lobby page
- [x] Drawing canvas and toolbar
- [x] Chat panel and guess input
- [x] Player list, timer, and word hint display
- [x] Word selection modal
- [x] Leaderboard and result screen
- [ ] Full responsive styling

### Final Stage
- [x] Frontend–backend integration
- [x] Backend and multiplayer testing
- [ ] Browser compatibility testing
- [ ] Deployment with HTTPS
- [ ] Final documentation and UML diagrams

---

## 📈 Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Low-latency drawing, near real-time chat, multiple concurrent rooms |
| **Security** | Input validation and HTTPS |
| **Reliability** | Stable, synchronised gameplay; handles disconnects gracefully |
| **Maintainability** | Modular architecture and documented code |
| **Scalability** | Multiple rooms and concurrent players |
| **Usability** | Simple, responsive, easy to use |
| **Compatibility** | Works on modern desktop browsers |

---

## ⚠️ Constraints and Assumptions

**Constraints**
- Needs a stable internet connection
- Browser must support HTML5 Canvas and JavaScript
- Depends on reliable WebSocket synchronisation

**Assumptions**
- Users have internet access and a supported browser
- The server stays online during gameplay
- Target devices are desktops and laptops (mobile is out of initial scope)
- Designed for small groups (up to six players per room)

---

## 🚧 Limitations

- Network delays or unstable connections can affect gameplay
- Player disconnections can interrupt a game
- The number of simultaneous players depends on server capacity
- Drawing tools are basic (no fill bucket or undo yet)

---

## 🔮 Future Enhancements

- Mobile and touch-screen support
- Public and private room listing
- Custom word lists
- Kick, ban, and vote-kick controls
- Sound effects and animations
- User accounts, profiles, achievements, and game history
- Fill-bucket tool and undo
- More game modes and drawing tools
- Multiple languages
- Stronger anti-cheating and security features


## 📄 References

1. [MDN Web Docs – WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
2. [OWASP – WebSocket Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html)
3. [FastAPI Documentation](https://fastapi.tiangolo.com/)
4. [React Documentation](https://react.dev/)
5. [HTML5 Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
6. IEEE SRS Standard

