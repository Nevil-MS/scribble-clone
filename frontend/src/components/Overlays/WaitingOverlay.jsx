import "./WaitingOverlay.css";

function WaitingOverlay() {
  return (
    <div className="canvas-overlay">
      <h2>Waiting for player to choose a word</h2>

      <div className="waiting-spinner"></div>

      <p>Please wait...</p>
    </div>
  );
}

export default WaitingOverlay;