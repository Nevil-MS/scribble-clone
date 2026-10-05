function ChoiceOverlay({ onChoose }) {
  const words = ["Apple", "Rocket", "Dragon"];

  return (
    <div
      className="canvas-overlay choice-overlay"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        width: "100%",
        height: "100%",
        boxSizing: "border-box",
        padding: "30px",
        gap: "20px",
      }}
    >
      <h2
        style={{
          margin: 0,
          textAlign: "center",
        }}
      >
        Choose a word
      </h2>

      <div
        className="word-buttons"
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
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