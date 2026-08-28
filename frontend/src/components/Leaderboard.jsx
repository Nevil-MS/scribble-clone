import "./Leaderboard.css";

function Leaderboard() {
  const players = [
    { rank: 1, name: "Player 1", points: 1440 },
    { rank: 2, name: "Player 2", points: 1230 },
    { rank: 3, name: "Player 3", points: 940 },
    { rank: 4, name: "Player 4", points: 850 },
    { rank: 5, name: "Player 5", points: 815 },
    { rank: 6, name: "Player 6", points: 0 },
  ];

  return (
    <div className="canvas-overlay leaderboard-overlay">
      <h1>Player 1 Wins!</h1>

      <div className="podium">
        <div className="podium-card second">
          <div className="avatar-placeholder">Avatar</div>
          <h2>#2</h2>
          <h3>{players[1].name}</h3>
          <p>{players[1].points} pts</p>
        </div>

        <div className="podium-card first">
          <div className="avatar-placeholder">Avatar</div>
          <h2>#1</h2>
          <h3>{players[0].name}</h3>
          <p>{players[0].points} pts</p>
        </div>

        <div className="podium-card third">
          <div className="avatar-placeholder">Avatar</div>
          <h2>#3</h2>
          <h3>{players[2].name}</h3>
          <p>{players[2].points} pts</p>
        </div>
      </div>

      <div className="leaderboard-rest">
        {players.slice(3).map((player) => (
          <div key={player.rank} className="mini-player">
            <div className="avatar-placeholder small">Avatar</div>
            <strong>#{player.rank}</strong>
            <span>{player.name}</span>
            <small>{player.points} pts</small>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LeaderboardOverlay;