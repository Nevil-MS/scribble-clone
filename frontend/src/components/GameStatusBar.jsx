import "./styles/GameStatusBar.css";
import IconPlaceholder from "./IconPlaceholder";

function GameStatusBar({
  round = 1,
  totalRounds = 3,
  status = "waiting",
  timeRemaining = null,
}) {
  return (
    <div className="game-status-bar">
      <div className="left-info">
        <div className="round-timer">
          <IconPlaceholder label="TM" />
          {timeRemaining !== null && (
            <span>{timeRemaining}</span>
          )}
        </div>

        <div className="round-info">
          Round {round} of {totalRounds}
        </div>
      </div>

      <div className="game-status">
        {status}
      </div>

      <div className="right-info">
        <button className="settings-btn">
          <IconPlaceholder label="ST" />
        </button>
      </div>
    </div>
  );
}

export default GameStatusBar;