function ChoiceOverlay({ onChoose }) {
  const words = ["Apple", "Rocket", "Dragon"];

  return (
    <div className="canvas-overlay choice-overlay">
      <h2>Choose a word</h2>

      <div className="word-buttons">
        {words.map((word) => (
          <button
            key={word}
            onClick={() => onChoose(word)}
          >
            {word}
          </button>
        ))}
      </div>
    </div>
  );
}

export default ChoiceOverlay;