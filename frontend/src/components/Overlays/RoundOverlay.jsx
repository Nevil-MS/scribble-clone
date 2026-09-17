import "./RoundOverlay.css";

function RoundOverlay({ round, totalRounds, player, onContinue }) {
  return (
    <div className="canvas-overlay round-overlay">
      <h1>Round {round}</h1>
      <p>{player} is drawing</p>

      <button onClick={onContinue}>Continue</button>
    </div>
  );
}

export default RoundOverlay;