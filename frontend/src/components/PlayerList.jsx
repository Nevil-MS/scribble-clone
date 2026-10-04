import "./styles/PlayerList.css";
import AvatarPlaceholder from "./AvatarPlaceholder";
function PlayerList() {
  return (
    <div className="player-list">
      <div className="player-info">
        <div className="player-position">#1</div>
        <div className="player-name">Player 1</div>
        <div className="player-points">0 points</div>
        <div className="player-avatar">
          <AvatarPlaceholder initials="P1" />
        </div>
      </div>

      <div className="player-info">
        <div className="player-position">#2</div>
        <div className="player-name">Player 2</div>
        <div className="player-points">0 points</div>
        <div className="player-avatar">
          <AvatarPlaceholder initials="P2" />
        </div>
      </div>

      <div className="player-info">
        <div className="player-position">#3</div>
        <div className="player-name">Player 3</div>
        <div className="player-points">0 points</div>
        <div className="player-avatar">
          <AvatarPlaceholder initials="P3" />
        </div>
      </div>
    </div>
  );
}

export default PlayerList;