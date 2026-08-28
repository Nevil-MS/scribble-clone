import { useState } from "react";
import GameTitle from "../components/GameTitle";
import GameStatusBar from "../components/GameStatusBar";
import PlayerList from "../components/PlayerList";
import Chat from "../components/Chat";
import ChooseWordOverlay from "../components/ChooseWordOverlay";
import WaitingOverlay from "../components/WaitingOverlay";
import "./GamePage.css";

function GamePage() {
  const [gameState, setGameState] = useState("waiting");
  // States: waiting | choosing | drawing

  return (
    <main>
      <div className="game-page">
        <GameTitle />
        <GameStatusBar />

        <div className="game-content">
          <PlayerList />

          <div className="canvas-section">
            <div className="drawing-area">
              <canvas
                id="drawing-board"
                width={800}
                height={500}
              ></canvas>
            </div>

            {gameState === "waiting" && <WaitingOverlay />}

            {gameState === "choosing" && (
              <ChooseWordOverlay
                onChoose={() => setGameState("drawing")}
              />
            )}

            <div
              className={`canvas-toolbar ${
                gameState !== "drawing" ? "toolbar-hidden" : ""
              }`}
            >
              <div className="tool-group">
                <button title="Pencil">✏</button>
                <button title="Eraser">⌫</button>
                <button title="Fill">▣</button>
              </div>

              <div className="brush-group">
                <button>•</button>
                <button>●</button>
                <button>⬤</button>
              </div>

              <div className="color-palette">
                <button className="white"></button>
                <button className="lightgrey"></button>
                <button className="grey"></button>
                <button className="black"></button>

                <button className="pink"></button>
                <button className="red"></button>
                <button className="orange"></button>
                <button className="brown"></button>

                <button className="yellow"></button>
                <button className="lime"></button>
                <button className="green"></button>
                <button className="cyan"></button>

                <button className="blue"></button>
                <button className="purple"></button>
              </div>
            </div>
          </div>

          <Chat />
        </div>
      </div>
    </main>
  );
}

export default GamePage;