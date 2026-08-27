import "./ChooseWordOverlay.css";

function ChooseWordOverlay() {
  const words = ["Apple", "Rocket", "Dragon"];

  return (
    <div className="canvas-overlay">
      <h2>Choose a word</h2>

      <div className="word-buttons">
        {words.map((word) => (
          <button key={word}>{word}</button>
        ))}
      </div>
    </div>
  );
}

export default ChooseWordOverlay;