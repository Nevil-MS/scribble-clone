import { useState } from "react";
import GameTitle from "../components/GameTitle";
import GameStatusBar from "../components/GameStatusBar";
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
  const [gameState, setGameState] = useState("drawing")

  // States: lobby | waiting | choosing | drawing | leaderboard

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

{gameState === "lobby" && <LobbyOverlay />}
{gameState === "waiting" && <WaitingOverlay />}
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