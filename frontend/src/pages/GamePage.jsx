import { useEffect, useRef, useState } from "react";
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

 function GamePage({ settings }) {
  const canvasRef = useRef(null);

  const [gameState, setGameState] = useState("round");
  const [tool, setTool] = useState("pencil");
const [color, setColor] = useState("#000000");
const [size, setSize] = useState(7);

  const [players, setPlayers] = useState([
    { id: 1, name: "Player 1", points: 0, initials: "P1" },
    { id: 2, name: "Player 2", points: 0, initials: "P2" },
    { id: 3, name: "Player 3", points: 0, initials: "P3" },
  ]);

  const [round, setRound] = useState(1);

  const [totalRounds, setTotalRounds] = useState(
    settings?.rounds ?? 3
  );

  const [gameStatus, setGameStatus] = useState("waiting");
  const [timeRemaining, setTimeRemaining] = useState(null);

  const [messages, setMessages] = useState([
    { id: 1, player: "Player 1", text: "Hello!" },
    { id: 2, player: "Player 2", text: "Hi!" },
  ]);

  function handleGameEvent(event) {
    switch (event.type) {
      case "LOBBY":
        setGameState("lobby");
        break;

      case "ROUND_STARTED":
        setGameState("round");
        setGameStatus("Round starting...");
        setTimeRemaining(null);
        break;

      case "WAITING":
        setGameState("waiting");
        setTimeRemaining(null);
        break;

      case "CHOOSING":
        setGameState("choosing");
        setGameStatus("Choosing word...");
        setTimeRemaining(null);
        break;

      case "DRAWING":
        setGameState("drawing");
        setGameStatus("Player 2 is drawing");
        setTimeRemaining(settings?.drawtime ?? 80);
        break;

      case "POINTS":
        setGameState("points");
        setGameStatus("Round complete");
        setTimeRemaining(null);
        break;

      case "LEADERBOARD":
        setGameState("leaderboard");
        setGameStatus("Game complete");
        setTimeRemaining(null);
        break;

      case "TIMER_EXPIRED":
        setGameState("points");
        setGameStatus("Round complete");
        setTimeRemaining(null);
        break;

      default:
        console.warn("Unknown game event:", event);
    }
  }

  // Drawing timer
  useEffect(() => {
    if (gameState !== "drawing" || timeRemaining === null) {
      return;
    }

    if (timeRemaining <= 0) {
      handleGameEvent({ type: "TIMER_EXPIRED" });
      return;
    }

    const timer = setTimeout(() => {
      setTimeRemaining((previous) => previous - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [gameState, timeRemaining]);

  // Move to next round or leaderboard after Points
  useEffect(() => {
    if (gameState !== "points") {
      return;
    }

    const timer = setTimeout(() => {
      if (round < totalRounds) {
        setRound((previous) => previous + 1);

        handleGameEvent({
          type: "ROUND_STARTED",
        });
      } else {
        handleGameEvent({
          type: "LEADERBOARD",
        });
      }
    }, 3000);

    return () => clearTimeout(timer);
  }, [gameState, round, totalRounds]);

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

        <div className="game-content">

          <PlayerList players={players} />

          <div className="canvas-column">

            <div className="canvas-section">

              <DrawingCanvas
              ref={canvasRef}
  round={round}
  color={color}
  size={size}
  tool={tool}
  onStroke={(stroke) => {
    console.log("Stroke to send:", stroke);
  }}
  onUndo={() => {
    console.log("Undo");
  }}
  onClear={() => {
    console.log("Clear");
  }}
/>

              {gameState === "points" && (
                <PointsOverlay />
              )}

              {gameState === "lobby" && (
                <LobbyOverlay
                  onStart={(settings) => {
                    console.log(
                      "Settings received by GamePage:",
                      settings
                    );

                    handleGameEvent({
                      type: "ROUND_STARTED",
                    });
                  }}
                />
              )}

              {gameState === "waiting" && (
                <WaitingOverlay />
              )}

              {gameState === "round" && (
                <RoundOverlay
                  round={round}
                  totalRounds={totalRounds}
                  player="Player 2"
                  onComplete={() =>
                    handleGameEvent({
                      type: "CHOOSING",
                    })
                  }
                />
              )}

              {gameState === "choosing" && (
                <ChoiceOverlay
                  onChoose={(word) => {
                    console.log("Word selected:", word);

                    handleGameEvent({
                      type: "DRAWING",
                    });
                  }}
                />
              )}

              {gameState === "leaderboard" && (
                <Leaderboard />
              )}

            </div>

            <CanvasToolbar
  hidden={gameState !== "drawing"}
  tool={tool}
  setTool={setTool}
  color={color}
  setColor={setColor}
  size={size}
  setSize={setSize}
  onUndo={() => canvasRef.current?.undo()}
  onClear={() => canvasRef.current?.clearCanvas()}
/>

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