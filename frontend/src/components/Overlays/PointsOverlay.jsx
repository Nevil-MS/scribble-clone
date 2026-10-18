import "./PointsOverlay.css";

function PointsOverlay({ players, word }) {

  return (
    <div className="canvas-overlay points-overlay">
      <p className="points-subtitle">The word was</p>

      <h1 className="points-word">{word || "Round complete"}</h1>

      <p className="points-message">
        Everyone guessed the word!
      </p>

      <div className="points-list">
        {players.map((player) => (
  <div className="points-row" key={player.id}>
    <span>{player.name}</span>
    <span className="score">{player.points}</span>
  </div>
))}
      </div>
    </div>
  );
}

export default PointsOverlay;