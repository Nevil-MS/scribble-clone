import { useState } from "react";
import GameTitle from "../components/GameTitle";
import GameStatusBar from "../components/GameStatusBar";
import PlayerList from "../components/PlayerList";
import Chat from "../components/Chat";
import "./GamePage.css";

function GamePage() {
  const [mode, setMode] = useState("choose");

  const words = ["Apple", "Rocket", "Dragon"];

  return (
    <main>
      <div className="game-page">
        <GameTitle />

        <GameStatusBar />

        <div className="game-content">
          <PlayerList />

          <div className="canvas-section">
            <canvas width={800} height={500}></canvas>

            {mode === "choose" && (
              <div className="canvas-overlay">
                <h2>Choose a word</h2>

                <div className="word-buttons">
                  {words.map((word) => (
                    <button
                      key={word}
                      onClick={() => setMode("draw")}
                    >
                      {word}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {mode === "waiting" && (
              <div className="canvas-overlay">
                <h2>Waiting for players...</h2>
                <p>Minimum 2 players required</p>
              </div>
            )}
          </div>

          <Chat />
        </div>
      </div>
    </main>
  );
}

export default GamePage;
