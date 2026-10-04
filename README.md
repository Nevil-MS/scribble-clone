# 🎨 Skribbl.io Clone – Online Multiplayer Drawing & Guessing Game

A real-time, web-based multiplayer game where one player draws a secret word and everyone else tries to guess it. Players join rooms, chat, earn points based on how fast they guess, and compete on a live leaderboad.


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
| **Database** | MongoDB |
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
```

- **REST (HTTPS):** room creation, joining, validation
- **WebSockets:** drawing strokes, chat, guesses, timers, scores, turn changes
- **Backend** keeps live room state in memory and uses MongoDB for persistent data (word bank, results)

---

## 🔄 Game Flow

```
Home Page → Create/Join Room → Lobby → Host Starts Game
      → Drawer Picks Word (1 of 3) → Drawing + Guessing (timer, hints)
      → Turn Ends → Scores Updated → Next Drawer
      → All Rounds Complete → Final Leaderboard & Winner
      → Replay / Return to Lobby
```

---

## 💻 Frontend Details

**Pages / Screens**
1. Home Page (username, avatar, create/join)
2. Lobby (players, settings, chat, start)
3. Game Screen (canvas, toolbar, chat panel, player list, timer, word hint)
4. Result Screen (final leaderboard, winner, replay)

**Main Components**
- `Canvas` – drawing area with mouse event handling
- `Toolbar` – brush, color picker, size slider, eraser, clear
- `ChatBox` – messages and guess input
- `PlayerList` – avatars, names, live scores, drawer indicator
- `Timer` and `WordHint`
- `WordSelectModal` – shown to the drawer
- `Leaderboard`

**Key Frontend Responsibilities**
- Capture drawing events and send them over WebSocket
- Render strokes received from other players
- Manage WebSocket connection and reconnection
- Responsive layout for desktop and laptop screens

---

## ⚙️ Backend Details

**Responsibilities**
- Create and validate rooms; generate unique room codes
- Manage WebSocket connections per room
- Broadcast drawing data, chat, and game events
- Control game state: lobby → playing → round end → results
- Assign drawers, serve random words, run timers, reveal hints
- Validate guesses and calculate scores
- Input validation and security checks

**Suggested REST Endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/rooms` | Create a room (returns room code) |
| POST | `/api/rooms/{code}/join` | Join a room |
| GET | `/api/rooms/{code}` | Get room details |
| WS | `/ws/{room_code}` | Real-time game connection |

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

**MongoDB Collections (proposed)**

- **rooms** – `room_code`, `host`, `max_players`, `rounds`, `timer`, `status`, `created_at`
- **players** – `username`, `avatar`, `room_code`, `score`
- **words** – `word`, `category`/`difficulty`
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

### Prerequisites
- Node.js (v18+) and npm
- Python 3.10+
- MongoDB (local or Atlas)
- Git

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

### 3. Frontend setup
```bash
cd frontend
npm install
npm start        # or: npm run dev (if using Vite)
```
Frontend runs at `http://localhost:3000` (or `5173` for Vite)

### 4. Environment variables
Create a `.env` file in `backend/`:
```
MONGO_URI=mongodb://localhost:27017
DB_NAME=skribbl_clone
```

---

## 📊 Project Status

### ✅ Completed
- [x] Project idea and topic finalization
- [x] Software Requirements Specification (SRS) – v1.0
- [x] Tech stack selection
- [x] Low-fidelity UI wireframes (Figma)

### 🔄 In Progress
- [ ] Project repository setup (GitHub)
- [ ] High-fidelity UI design

### ⏳ Remaining

**Frontend**
- [ ] Home page (username, avatar, create/join)
- [ ] Lobby page
- [ ] Drawing canvas + toolbar
- [ ] Chat panel and guess input
- [ ] Player list, timer, word hint display
- [ ] Word selection modal
- [ ] Leaderboard and result screen
- [ ] Responsive styling

**Backend**
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

**Final Stage**
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

**Constraints**
- Requires a stable internet connection
- Browser must support HTML5 Canvas and JavaScript
- Depends on reliable WebSocket synchronization

**Assumptions**
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

## 👥 Team

| Name | Role |
|------|------|
| _Your Name_ | _Role_ |
| _Team Member_ | _Role_ |

---

## 📄 References
- IEEE SRS Standard
- HTML5 Canvas API
- React, FastAPI, MongoDB documentation

---

## 📜 License
This project is developed for educational purposes. Add a license (e.g., MIT) if you plan to publish it.
