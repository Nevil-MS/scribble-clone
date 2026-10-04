import "./styles/PlayerList.css";
import AvatarPlaceholder from "./AvatarPlaceholder";

const defaultPlayers = [
  { id: 1, name: "Player 1", points: 0, initials: "P1" },
  { id: 2, name: "Player 2", points: 0, initials: "P2" },
  { id: 3, name: "Player 3", points: 0, initials: "P3" },
];

function PlayerList({ players = defaultPlayers }) {
  return (
    <div className="player-list">
      {players.map((player, index) => (
        <div className="player-info" key={player.id}>
          <div className="player-position">#{index + 1}</div>

          <div className="player-name">
            {player.name}
          </div>

          <div className="player-points">
            {player.points} points
          </div>

          <div className="player-avatar">
            <AvatarPlaceholder
              initials={player.initials || `P${index + 1}`}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export default PlayerList;