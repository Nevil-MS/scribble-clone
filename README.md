#  Skribbl.io Clone – Online Multiplayer Drawing & Guessing Game

A real-time, web-based multiplayer game where one player draws a secret word and everyone else tries to guess it. Players join rooms, chat, earn points based on how fast they guess, and compete on a live leaderboard.


## 📌 Project Overview

| Item | Details |
|------|---------|
| **Project Name** | Skribbl.io Clone |
| **Type** | Real-time multiplayer web game |
| **Purpose** | Let users draw and guess words together in real time |
| **Users** | Players and Hosts |
| **Design Tool** | Figma (low-fidelity wireframes completed) |
| **Dev Tools** | Visual Studio Code, Git, GitHub |

**Scope:** Users enter a username, pick an avatar, create or join a room, draw and guess words in real time, chat, earn points, and view leaderboards.

### Definitions

- **Host** – creates and manages the room and its settings
- **Player** – participates in the game (draws, guesses, chats)
- **Drawer** – the player currently drawing the chosen word
- **Round** – one complete drawing turn
- **Leaderboard** – ranking of players by score

---

## ✨ Key Features

### 1. Home Page
- Enter a username
- Choose an avatar
- Create a room or join an existing room using a room code

### 2. Room Management
- Auto-generated unique room code
- Host configures: **number of players**, **number of rounds**, **drawing timer**

### 3. Lobby
- Live list of players and the host
- Room settings display
- Lobby chat
- Start-game button (host only)

### 4. Word Selection
- Drawer chooses **1 of 3 random words**
- If the drawer doesn't choose in time, a word is **auto-selected**

### 5. Drawing Canvas (HTML5 Canvas)
- Brush tool with multiple colors
- Adjustable brush size
- Eraser
- Clear canvas
- **Real-time synchronization** of strokes to all players

### 6. Gameplay
- Automatic drawer assignment each turn
- Guess acceptance and validation
- Progressive **hints** (letters revealed over time)
- Turn timer
- Turn switching and round completion

### 7. Chat & Scoring
- Real-time chat
- Guess validation (correct guesses are hidden from other players)
- Live score updates
- Leaderboard and winner announcement

### 8. Game Management
- Final results screen
- Replay option
- Host controls
- Return to lobby

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React, JavaScript (ES6+), HTML5, CSS3, HTML5 Canvas API |
| **Backend** | Python, FastAPI, Uvicorn (ASGI server) |
| **Real-time** | WebSockets |
| **Database** | SQLite |
| **Communication** | WebSockets + HTTPS |
| **Design** | Figma |
| **Tools** | VS Code, Git, GitHub |

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
                                                  │     MongoDB      │
                                                  │ (Rooms, Words,   │
                                                  │  Scores)         │
                                                  └──────────────────┘


- **REST (HTTPS):** room creation, joining, validation
- **WebSockets:** drawing strokes, chat, guesses, timers, scores, turn changes
- **Backend** keeps live room state in memory and uses MongoDB for persistent data (word bank, results)


## 🔄 Game Flow

```
Home Page → Create/Join Room → Lobby → Host Starts Game
      → Drawer Picks Word (1 of 3) → Drawing + Guessing (timer, hints)
      → Turn Ends → Scores Updated → Next Drawer
      → All Rounds Complete → Final Leaderboard & Winner
      → Replay / Return to Lobby



## 💻 Frontend Details

### Pages / Screens
1. Home Page (username, avatar, create/join)
2. Lobby (players, settings, chat, start)
3. Game Screen (canvas, toolbar, chat panel, player list, timer, word hint)
4. Result Screen (final leaderboard, winner, replay)

### Main Components
- `Canvas` – drawing area with mouse event handling
- `Toolbar` – brush, color picker, size slider, eraser, clear
- `ChatBox` – messages and guess input
- `PlayerList` – avatars, names, live scores, drawer indicator
- `Timer` and `WordHint`
- `WordSelectModal` – shown to the drawer
- `Leaderboard`

### Key Frontend Responsibilities
- Capture drawing events and send them over WebSocket
- Render strokes received from other players
- Manage WebSocket connection and reconnection
- Responsive layout for desktop and laptop screens

---

## ⚙️ Backend Details

### Responsibilities
- Create and validate rooms; generate unique room codes
- Manage WebSocket connections per room
- Broadcast drawing data, chat, and game events
- Control game state: lobby → playing → round end → results
- Assign drawers, serve random words, run timers, reveal hints
- Validate guesses and calculate scores
- Input validation and security checks

### Suggested REST Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/rooms` | Create a room (returns room code) |
| POST | `/api/rooms/{code}/join` | Join a room |
| GET | `/api/rooms/{code}` | Get room details |
| WS | `/ws/{room_code}` | Real-time game connection |

---

### 🌐 Networking Module – Work Completed

#### 1. WebSocket Communication
- Implemented WebSocket-based real-time communication using FastAPI WebSockets.
- Established connections between clients and the game server.
- Added connection and disconnection handling.
- Added unique player IDs for WebSocket connections.
- Implemented message-based communication between clients and server.

#### 2. Message Routing
Implemented server-side routing for different client messages:

- `join`
- `reconnect`
- `chat`
- `select_word`
- `draw`
- `lobby_update`
- `start_game`

And server responses/events such as:

- `game_state`
- `word_options`
- `chat`
- `system_message`
- `timer`
- `leaderboard`
- `draw`
- `player_joined`
- `player_left`
- `error`
- `connection`

#### 3. Player Join & Room Management
- Implemented player joining through WebSockets.
- Added player name and avatar validation.
- Connected players are maintained per room.
- Added host assignment.
- Added room/player capacity validation.
- Added notifications when players join.
- Prevented invalid/duplicate player connections.

#### 4. Late Joining
- Implemented support for players joining while a game is already running.
- Late players can join the current game without interrupting the ongoing turn.
- Late joiners participate as guessers in the current turn.
- Added them to future turn order.
- Synchronized their current game state after joining.

#### 5. Reconnection
- Implemented player reconnection using the existing player ID.
- Reconnection restores the existing player instead of creating a duplicate.
- Reconnected players receive the current game state.
- Word visibility is restored according to the player's role:
  - Drawer → full word
  - Correct guesser → full word
  - Other guessers → word pattern

#### 6. Disconnect & Grace Period
- Implemented player disconnect handling.
- Added a 30-second reconnection grace period.
- Disconnected players continue occupying their slot during the grace period.
- Players can reconnect using the same ID.
- Players are permanently removed after the grace period expires.
- Other players are notified about temporary disconnections and permanent removals.
- Host transfer is handled when the host permanently leaves.

#### 7. Chat & Guess Networking
- Integrated WebSocket chat with the existing `GameEngine.process_guess()`.
- Removed server-side chat history/storage from networking.
- Messages are classified through the game engine as:
  - Normal chat
  - Close guess
  - Wrong guess
  - Correct guess
- Implemented recipient filtering so different players see appropriate messages.
- Correct guesses are privately acknowledged to the correct player and announced appropriately to others.
- Already-correct players' messages are hidden from players who are still guessing when required.

#### 8. Word Visibility
Implemented player-specific word visibility:

- Drawer receives the complete word.
- Guessers receive the hidden word pattern.
- Correct guesser receives the complete word.
- Remaining guessers continue seeing the updated pattern.
- Everyone receives the complete word when the turn ends.
- Word visibility is also restored correctly after reconnection.

#### 9. Word Selection Networking
- Added communication for word options.
- Word options are sent only to the drawer.
- Drawer selects a word through WebSocket.
- Selected word is synchronized with the other players through appropriate visibility rules.
- Added a 15-second word-selection timer.
- Added automatic word selection when the drawer does not select within the allowed time.

#### 10. Real-Time Drawing
- Implemented WebSocket relay for drawing data.
- Drawing data from the drawer is forwarded to other connected players.
- Only the current drawer is allowed to send drawing updates.

#### 11. Game Timers
Implemented real-time timers through asynchronous networking tasks:

| Timer | Duration |
|-------|----------|
| Round-start countdown | 3 seconds |
| Word-selection countdown | 15 seconds |
| Drawing/guessing timer | Configurable, default 80 seconds |
| Leaderboard display | 7 seconds |

- Timer updates are broadcast to clients every second.
- Turn automatically ends when the drawing timer expires.

#### 12. Automatic Hint Synchronization
- Added networking support for automatic hints.
- Hints are distributed during the drawing timer.
- Hint timing is calculated based on the allowed number of hints.
- Updated word patterns are broadcast to players after each hint.
- Uses the existing `GameEngine.reveal_hint()` logic.

#### 13. Turn & Round Synchronization
Networking coordinates transitions between:

- Round start
- Word selection
- Drawing/guessing
- Turn end
- Leaderboard
- Next turn
- Next round
- Game end

The server broadcasts updated game state after important state changes.

#### 14. Game State Synchronization
Clients receive synchronized information about:

- Players
- Player connection status
- Host
- Game settings
- Current round
- Current turn
- Current drawer
- Game state
- Player-specific word information
- Leaderboard information

#### 15. Lobby Updates
- Implemented host-controlled lobby updates through WebSocket.
- Added validation for lobby settings.
- Prevented player capacity from being reduced below the number of persistent players.
- Settings are synchronized with connected clients.

#### 16. Error Handling
Added WebSocket error responses for invalid actions. Handles:

- Invalid room
- Invalid player
- Invalid word selection
- Unauthorized actions
- Invalid game states
- Invalid profile information
- Non-drawer drawing attempts
- Non-host lobby/game-start actions

#### 17. Asynchronous Runtime Management
Added background tasks for:

- Turn timers
- Word-selection timers
- Round transitions
- Leaderboard countdown
- Automatic hints
- Disconnect grace periods

Added task cancellation to prevent old timers from affecting later turns.

#### 18. Networking Testing
- Created/updated WebSocket testing to automatically create a room.
- Tested:
  - Room creation
  - WebSocket connection
  - Player joining
  - Host assignment
  - Game start
  - Round countdown
  - Word selection
  - Drawer/guesser word visibility
  - Correct guessing
  - Game-state synchronization
- Verified backend Python files compile successfully.

---

## 🔌 WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `join_room` | Client → Server | Player joins a room |
| `player_list` | Server → Clients | Updated list of players |
| `start_game` | Client → Server | Host starts the game |
| `word_options` | Server → Drawer | 3 random words to choose from |
| `word_selected` | Client → Server | Drawer's chosen word |
| `draw` | Client ⇄ Server | Stroke data (x, y, color, size) |
| `clear_canvas` | Client ⇄ Server | Clear the canvas |
| `chat_message` | Client ⇄ Server | Chat message |
| `guess` | Client → Server | Player's guess |
| `correct_guess` | Server → Clients | Announces a correct guess + score |
| `hint_update` | Server → Clients | Reveals another letter |
| `timer_update` | Server → Clients | Remaining time |
| `turn_end` | Server → Clients | Turn finished, reveal word |
| `game_over` | Server → Clients | Final leaderboard + winner |

---

## 🗄 Database Design

- **rooms** – `room_code`, `host`, `max_players`, `rounds`, `timer`, `status`, `created_at`
- **players** – `username`, `avatar`, `room_code`, `score`
- **words** – `word`, `category` / `difficulty`
- **game_results** – `room_code`, `final_scores`, `winner`, `played_at`

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
```

---

## 🚀 Installation & Setup

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/skribbl-clone.git
cd skribbl-clone
```

### 2. Backend setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```
Backend runs at `http://localhost:8000`

---

## 📊 Project Status

### Frontend
- [ ] Home page (username, avatar, create/join)
- [ ] Lobby page
- [ ] Drawing canvas + toolbar
- [ ] Chat panel and guess input
- [ ] Player list, timer, word hint display
- [ ] Word selection modal
- [ ] Leaderboard and result screen
- [ ] Responsive styling

### Backend
- [ ] FastAPI project setup
- [ ] Room creation and joining APIs
- [ ] WebSocket connection manager
- [ ] Real-time drawing synchronization
- [ ] Game state management (turns, rounds, timers)
- [ ] Word bank and random word selection
- [ ] Guess validation and scoring logic
- [ ] Hint reveal system
- [ ] MongoDB integration
- [ ] Input validation

### Final Stage
- [ ] Frontend–backend integration
- [ ] Multi-room and multi-player testing
- [ ] Browser compatibility testing
- [ ] Bug fixing and optimization
- [ ] Deployment with HTTPS
- [ ] Final documentation, UML diagrams (Use Case, Activity)

---

## 📈 Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Low-latency drawing; near real-time chat; multiple concurrent rooms |
| **Security** | Input validation and HTTPS |
| **Reliability** | Stable, synchronized gameplay between players |
| **Maintainability** | Modular architecture, documented code, easy updates |
| **Scalability** | Multiple game rooms and concurrent players |
| **Usability** | Simple, responsive, easy to use |
| **Compatibility** | Works across modern desktop browsers |

---

## ⚠️ Constraints & Assumptions

### Constraints
- Requires a stable internet connection
- Browser must support HTML5 Canvas and JavaScript
- Depends on reliable WebSocket synchronization

### Assumptions
- Users have internet access and a supported browser
- The server remains online during gameplay
- Target devices are desktops/laptops (mobile not in the initial scope)

---

## 🔮 Future Enhancements

- Mobile and touch-screen support
- Private/public room listing
- Custom word lists
- Kick/ban and vote-kick controls
- Sound effects and animations
- User accounts and persistent stats
- Fill-bucket tool and undo
- Multiple languages

---

## 📄 References

- IEEE SRS Standard
- HTML5 Canvas API
- React, FastAPI, MongoDB documentation
