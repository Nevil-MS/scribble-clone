import "./Leaderboard.css";

function Leaderboard({ players = [] }) {

  return (
    <div className="canvas-overlay leaderboard">
      <h1>{players[0]?.name ?? "Game Over"} Wins!</h1>

      <div className="podium">
        <div className="podium-card second">
          <div className="avatar-placeholder">Avatar</div>
<h2>#2</h2>
<h3>{players[1]?.name ?? "—"}</h3>
<p>{players[1]?.points ?? 0} pts</p>
        </div>

        <div className="podium-card first">
          <div className="avatar-placeholder">Avatar</div>
<h2>#1</h2>
<h3>{players[0]?.name ?? "—"}</h3>
<p>{players[0]?.points ?? 0} pts</p>
        </div>

        <div className="podium-card third">
          <div className="avatar-placeholder">Avatar</div>
<h2>#3</h2>
<h3>{players[2]?.name ?? "—"}</h3>
<p>{players[2]?.points ?? 0} pts</p>
        </div>
      </div>

      <div className="leaderboard-rest">
        {players.slice(3).map((player, index) => (
  <div key={player.pid} className="mini-player">
    <div className="avatar-placeholder small">Avatar</div>
    <strong>#{player.position ?? index + 4}</strong>
    <span>{player.name}</span>
    <small>{player.points} pts</small>
  </div>
))}
      </div>
    </div>
  );
}

export default Leaderboard;