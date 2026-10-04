import "./styles/WaitingOverlay.css";
function WaitingOverlay() {
  return (
    <div className="canvas-overlay waiting-overlay">
      <h2>Player 1 is choosing a word!</h2>

      <div className="waiting-avatar">Avatar</div>
    </div>
  );
}

export default WaitingOverlay;