import GameTitle from "../components/GameTitle";
import "./LandingPage.css";

function LandingPage() {
  return (
    <main>
      <GameTitle />

      <div className="player-setup">
        <div className="name-lang">
          <input placeholder="Enter your name" />

          <select defaultValue="en">
            <option value="en">English</option>
          </select>
        </div>

        <div className="avatar-setup">
          <button>prev</button>

          <div className="avatar-placeholder">Avatar</div>

          <button>next</button>
        </div>

        <button className="play-btn">Play!</button>
      </div>
    </main>
  );
}

export default LandingPage;
