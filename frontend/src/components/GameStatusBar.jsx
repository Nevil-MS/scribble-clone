import "./styles/GameStatusBar.css";
import IconPlaceholder from "./IconPlaceholder";

function GameStatusBar() {
  return (
    <div className="game-status-bar">
      <div className="left-info">
        <div className="round-timer">
  <IconPlaceholder label="TM" />
</div>

        <div className="round-info">Round 1 of 3</div>
      </div>

      <div className="game-status">waiting</div>

      <div className="right-info">
        <button className="settings-btn">
          <IconPlaceholder label="ST" />
        </button>
      </div>
    </div>
  );
}

export default GameStatusBar;