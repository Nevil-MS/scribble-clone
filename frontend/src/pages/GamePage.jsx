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

  // States: lobby | round | waiting | choosing | drawing | leaderboard | points

  return (
    <main>
      <div className="game-page">
        <GameTitle />
        <GameStatusBar />

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
            <button onClick={() => setGameState("lobby")}>Lobby</button>
            <button onClick={() => setGameState("round")}>Round</button>
            <button onClick={() => setGameState("waiting")}>Waiting</button>
            <button onClick={() => setGameState("choosing")}>Choose</button>
            <button onClick={() => setGameState("drawing")}>Draw</button>
            <button onClick={() => setGameState("points")}>Points</button>
            <button onClick={() => setGameState("leaderboard")}>Board</button>
          </div>
        )}

        <div className="game-content">
          <PlayerList />

          <div className="canvas-column">
            <div className="canvas-section">
              <DrawingCanvas />

              {gameState === "points" && <PointsOverlay />}

              {gameState === "lobby" && (
                <LobbyOverlay onStart={() => setGameState("round")} />
              )}

              {gameState === "waiting" && <WaitingOverlay />}

              {gameState === "round" && (
                <RoundOverlay
                  round={1}
                  totalRounds={3}
                  player="Player 2"
                  onContinue={() => setGameState("choosing")}
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