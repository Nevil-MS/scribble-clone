import { useState } from "react";
import GameTitle from "../components/GameTitle";
import PointsOverlay from "../components/Overlays/PointsOverlay";
import GameStatusBar from "../components/GameStatusBar";
import RoundOverlay from "../components/Overlays/RoundOverlay";
import LobbyOverlay from "../components/LobbyOverlay";
import PlayerList from "../components/PlayerList";
import Chat from "../components/Chat";
import CanvasToolbar from "../components/CanvasToolbar";
import ChoiceOverlay from "../components/Overlays/ChoiceOverlay";
import WaitingOverlay from "../components/Overlays/WaitingOverlay";
import DrawingCanvas from "../components/DrawingCanvas";
import Leaderboard from "../components/Leaderboard";
import "./GamePage.css";

function GamePage() {
  const [gameState, setGameState] = useState("choosing");
  const [debug] = useState(true);

  const [players, setPlayers] = useState([
    { id: 1, name: "Player 1", points: 0, initials: "P1" },
    { id: 2, name: "Player 2", points: 0, initials: "P2" },
    { id: 3, name: "Player 3", points: 0, initials: "P3" },
  ]);

  const [round, setRound] = useState(1);
  const [totalRounds, setTotalRounds] = useState(3);
  const [gameStatus, setGameStatus] = useState("waiting");
  const [timeRemaining, setTimeRemaining] = useState(null);

  const [messages, setMessages] = useState([
    { id: 1, player: "Player 1", text: "Hello!" },
    { id: 2, player: "Player 2", text: "Hi!" },
  ]);

  // Central place for game-state transitions.
  // The networking layer can use these game events later.
  function handleGameEvent(event) {
    switch (event.type) {
      case "LOBBY":
        setGameState("lobby");
        break;

      case "ROUND_STARTED":
        setGameState("round");
        break;

      case "WAITING":
        setGameState("waiting");
        break;

      case "CHOOSING":
        setGameState("choosing");
        break;

      case "DRAWING":
        setGameState("drawing");
        break;

      case "POINTS":
        setGameState("points");
        break;

      case "LEADERBOARD":
        setGameState("leaderboard");
        break;

      case "TIMER_EXPIRED":
        setGameState("leaderboard");
        break;

      default:
        console.warn("Unknown game event:", event);
    }
  }

  return (
    <main>
      <div className="game-page">
        <GameTitle />

        <GameStatusBar
          round={round}
          totalRounds={totalRounds}
          status={gameStatus}
          timeRemaining={timeRemaining}
        />

        <select
          value={gameState}
          onChange={(e) => setGameState(e.target.value)}
        >
          <option value="lobby">Lobby</option>
          <option value="round">Round</option>
          <option value="waiting">Waiting</option>
          <option value="choosing">Choosing</option>
          <option value="drawing">Drawing</option>
          <option value="points">Points</option>
          <option value="leaderboard">Leaderboard</option>
        </select>

        {debug && (
          <div className="debug-nav">
            <button onClick={() => handleGameEvent({ type: "LOBBY" })}>
              Lobby
            </button>

            <button onClick={() => handleGameEvent({ type: "ROUND_STARTED" })}>
              Round
            </button>

            <button onClick={() => handleGameEvent({ type: "WAITING" })}>
              Waiting
            </button>

            <button onClick={() => handleGameEvent({ type: "CHOOSING" })}>
              Choose
            </button>

            <button onClick={() => handleGameEvent({ type: "DRAWING" })}>
              Draw
            </button>

            <button onClick={() => handleGameEvent({ type: "POINTS" })}>
              Points
            </button>

            <button onClick={() => handleGameEvent({ type: "LEADERBOARD" })}>
              Board
            </button>

            <button
              onClick={() => handleGameEvent({ type: "TIMER_EXPIRED" })}
            >
              Timer End
            </button>
          </div>
        )}

        <div className="game-content">
          <PlayerList players={players} />

          <div className="canvas-column">
            <div className="canvas-section">
              <DrawingCanvas
                onStroke={(stroke) => {
                  console.log("Stroke to send:", stroke);
                }}
              />

              {gameState === "points" && <PointsOverlay />}

              {gameState === "lobby" && (
                <LobbyOverlay
                  onStart={(settings) => {
                    console.log(
                      "Settings received by GamePage:",
                      settings
                    );

                    handleGameEvent({ type: "ROUND_STARTED" });
                  }}
                />
              )}

              {gameState === "waiting" && <WaitingOverlay />}

              {gameState === "round" && (
                <RoundOverlay
                  round={round}
                  totalRounds={totalRounds}
                  player="Player 2"
                  onContinue={() =>
                    handleGameEvent({ type: "CHOOSING" })
                  }
                />
              )}

              {gameState === "choosing" && (
                <ChoiceOverlay
                  onChoose={(word) => {
                    console.log("Word selected:", word);

                    handleGameEvent({ type: "DRAWING" });
                  }}
                />
              )}

              {gameState === "leaderboard" && <Leaderboard />}
            </div>

            <CanvasToolbar hidden={gameState !== "drawing"} />
          </div>

          <Chat
            messages={messages}
            onSendMessage={(text) => {
              console.log("Message to send:", text);
            }}
          />
        </div>
      </div>
    </main>
  );
}

export default GamePage;