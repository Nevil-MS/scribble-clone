import "./ChoiceOverlay.css";

// onChoose function is brought from the GamePage
function ChoiceOverlay({ onChoose }) {
  const words = ["Apple", "Rocket", "Dragon"];

  // This will eventually be chosen randomly from a stored word list
  return (
    <div className="canvas-overlay choice-overlay">
      <h2>Choose a word</h2>

      <div className="word-buttons">
        {words.map((word) => (
          <button key={word} onClick={onChoose}>
            {word}
          </button>
        ))}

        {/* Goes through the list "words" and creates one button for each word */}
      </div>
    </div>
  );
}

export default ChoiceOverlay;