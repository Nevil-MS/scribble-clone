import "./LobbyOverlay.css";
import IconPlaceholder from "./IconPlaceholder";

function LobbyOverlay({ onStart }) {
  return (
    <div className="canvas-overlay lobby-overlay">
      <div className="lobby-settings">

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="PL" />
            <label>Players</label>
          </div>
          <select><option>2</option></select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="LG" />
            <label>Language</label>
          </div>
          <select><option>English</option></select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="TM" />
            <label>Drawtime</label>
          </div>
          <select><option>80</option></select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="RD" />
            <label>Rounds</label>
          </div>
          <select><option>3</option></select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="WC" />
            <label>Word Count</label>
          </div>
          <select><option>3</option></select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="HT" />
            <label>Hints</label>
          </div>
          <select><option>2</option></select>
        </div>

        <div className="setting-row textarea-row">
          <div className="setting-label">
            <IconPlaceholder label="CW" />
            <label>Custom words</label>
          </div>

          <div className="custom-toggle">
            <label>
              <input type="checkbox" />
              Use custom words only
            </label>
          </div>

          <textarea placeholder="Minimum of 10 words..." />
        </div>

        <div className="lobby-buttons">
          <button onClick={onStart}>Start!</button>
          <button>Invite</button>
        </div>

      </div>
    </div>
  );
}

export default LobbyOverlay;