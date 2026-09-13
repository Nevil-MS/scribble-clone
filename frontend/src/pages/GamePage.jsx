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
  const [gameState, setGameState] = useState("lobby");

// States: lobby | round | waiting | choosing | drawing | leaderboard | points
  return (
    <main>
      <div className="game-page">
        <GameTitle />
        <GameStatusBar />

        <div className="game-content">
          <PlayerList />

          <div className="canvas-column">
            <div className="canvas-section">
              <DrawingCanvas />
{gameState === "points" && <PointsOverlay />}
{gameState === "lobby" && <LobbyOverlay />}
{gameState === "waiting" && <WaitingOverlay />}
{gameState === "round" && (
  <RoundOverlay
    round={1}
    totalRounds={3}
    player="Player 2"
  />
)}
{gameState === "choosing" && (
  <ChoiceOverlay onChoose={() => setGameState("drawing")} />
)}
{gameState === "leaderboard" && <Leaderboard />}
            </div>

            <CanvasToolbar hidden={gameState !== "drawing"} />
          </div>

          <Chat />
        </div>
      </div>
    </main>
  );
}

export default GamePage;