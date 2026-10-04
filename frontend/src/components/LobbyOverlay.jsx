import { useState } from "react";
import "./LobbyOverlay.css";
import IconPlaceholder from "./IconPlaceholder";

function LobbyOverlay({ onStart }) {
  const [settings, setSettings] = useState({
    players: 2,
    language: "English",
    drawtime: 80,
    rounds: 3,
    wordCount: 3,
    hints: 2,
    customWordsOnly: false,
    customWords: "",
  });

  function handleChange(setting, value) {
    setSettings((previous) => ({
      ...previous,
      [setting]: value,
    }));
  }

  function handleStart() {
    console.log("Lobby settings:", settings);
    onStart(settings);
  }

  return (
    <div className="canvas-overlay lobby-overlay">
      <div className="lobby-settings">

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="PL" />
            <label>Players</label>
          </div>

          <select
            value={settings.players}
            onChange={(e) =>
              handleChange("players", Number(e.target.value))
            }
          >
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={4}>4</option>
            <option value={5}>5</option>
            <option value={6}>6</option>
          </select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="LG" />
            <label>Language</label>
          </div>

          <select
            value={settings.language}
            onChange={(e) =>
              handleChange("language", e.target.value)
            }
          >
            <option>English</option>
          </select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="TM" />
            <label>Drawtime</label>
          </div>

          <select
            value={settings.drawtime}
            onChange={(e) =>
              handleChange("drawtime", Number(e.target.value))
            }
          >
            <option value={60}>60</option>
            <option value={80}>80</option>
            <option value={100}>100</option>
            <option value={120}>120</option>
          </select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="RD" />
            <label>Rounds</label>
          </div>

          <select
            value={settings.rounds}
            onChange={(e) =>
              handleChange("rounds", Number(e.target.value))
            }
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={4}>4</option>
            <option value={5}>5</option>
          </select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="WC" />
            <label>Word Count</label>
          </div>

          <select
            value={settings.wordCount}
            onChange={(e) =>
              handleChange("wordCount", Number(e.target.value))
            }
          >
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={4}>4</option>
            <option value={5}>5</option>
          </select>
        </div>

        <div className="setting-row">
          <div className="setting-label">
            <IconPlaceholder label="HT" />
            <label>Hints</label>
          </div>

          <select
            value={settings.hints}
            onChange={(e) =>
              handleChange("hints", Number(e.target.value))
            }
          >
            <option value={0}>0</option>
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
          </select>
        </div>

        <div className="setting-row textarea-row">
          <div className="setting-label">
            <IconPlaceholder label="CW" />
            <label>Custom words</label>
          </div>

          <div className="custom-toggle">
            <label>
              <input
                type="checkbox"
                checked={settings.customWordsOnly}
                onChange={(e) =>
                  handleChange(
                    "customWordsOnly",
                    e.target.checked
                  )
                }
              />
              Use custom words only
            </label>
          </div>

          <textarea
            placeholder="Minimum of 10 words..."
            value={settings.customWords}
            onChange={(e) =>
              handleChange("customWords", e.target.value)
            }
          />
        </div>

        <div className="lobby-buttons">
          <button onClick={handleStart}>Start!</button>
          <button>Invite</button>
        </div>

      </div>
    </div>
  );
}

export default LobbyOverlay;