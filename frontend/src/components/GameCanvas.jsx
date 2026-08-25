import { useState } from "react";
import "./GameCanvas.css";

function GameCanvas() {
  // waiting | choosing | drawing
  const [mode, setMode] = useState("waiting");

  const words = ["Apple", "Rocket", "Dragon"];

  return (
    <div className="canvas-container">
      <canvas width={800} height={500}></canvas>

      {mode === "waiting" && (
        <div className="canvas-overlay">
          <h2>Waiting for players...</h2>
          <p>Minimum 2 players required</p>

          {/* Demo button - remove later */}
          <button onClick={() => setMode("choosing")}>
            Continue
          </button>
        </div>
      )}

      {mode === "choosing" && (
        <div className="canvas-overlay">
          <h2>Choose a word</h2>

          <div className="word-options">
            {words.map((word) => (
              <button
                key={word}
                onClick={() => setMode("drawing")}
              >
                {word}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default GameCanvas;
