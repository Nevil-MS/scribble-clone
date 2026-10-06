import { useState } from "react";
import GameTitle from "../components/GameTitle";
import "./LandingPage.css";

function LandingPage({ onPlay }) {
  const [playerName, setPlayerName] = useState("");

  return (
    <main>
      <GameTitle />

      <div className="player-setup">
        <div className="name-lang">
          <input
            placeholder="Enter your name"
            value={playerName}
            onChange={(e) => setPlayerName(e.target.value)}
          />

          <select defaultValue="en">
            <option value="en">English</option>
          </select>
        </div>

        <div className="avatar-setup">
          <button>prev</button>

          <div className="avatar-placeholder">Avatar</div>

          <button>next</button>
        </div>

        <button
          className="play-btn"
          onClick={() => onPlay(playerName)}
        >
          Play!
        </button>
      </div>
    </main>
  );
}

export default LandingPage;