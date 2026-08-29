import "./LobbyOverlay.css";
function LobbyOverlay() {
  return (
    <div className="canvas-overlay lobby-overlay">
      <div className="lobby-settings">
        <div className="setting-row">
          <label>Players</label>
          <select><option>2</option></select>
        </div>

        <div className="setting-row">
          <label>Language</label>
          <select><option>English</option></select>
        </div>

        <div className="setting-row">
          <label>Drawtime</label>
          <select><option>80</option></select>
        </div>

        <div className="setting-row">
          <label>Rounds</label>
          <select><option>3</option></select>
        </div>

        <div className="setting-row">
          <label>Word Count</label>
          <select><option>3</option></select>
        </div>

        <div className="setting-row">
          <label>Hints</label>
          <select><option>2</option></select>
        </div>

        <label>Custom words</label>
        <textarea placeholder="Minimum of 10 words..." />

        <div className="lobby-buttons">
          <button>Start!</button>
          <button>Invite</button>
        </div>
      </div>
    </div>
  );
}

export default LobbyOverlay;