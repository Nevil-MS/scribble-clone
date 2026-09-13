import "./PointsOverlay.css";

function PointsOverlay() {
  const scores = [
    { name: "Player 1", points: 130 },
    { name: "Player 2", points: 35 },
  ];

  return (
    <div className="canvas-overlay points-overlay">
      <p className="points-subtitle">The word was</p>

      <h1 className="points-word">MAGIC WAND</h1>

      <p className="points-message">
        Everyone guessed the word!
      </p>

      <div className="points-list">
        {scores.map((player) => (
          <div className="points-row" key={player.name}>
            <span>{player.name}</span>
            <span className="score">+{player.points}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PointsOverlay;