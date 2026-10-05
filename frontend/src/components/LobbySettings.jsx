import { useState } from "react";
import "./styles/LobbySettings.css";

function LobbySettings({ onStart }) {
    const [settings, setSettings] = useState({
        players: 2,
        language: "English",
        drawtime: 80,
        rounds: 3,
        wordCount: 3,
        hints: 2,
    });

    function handleChange(setting, value) {
        setSettings((previous) => ({
            ...previous,
            [setting]: value,
        }));
    }

    return (
        <div className="lobby-settings">

            <div className="settings-scroll">

                <label>Players</label>
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

                <label>Language</label>
                <select
                    value={settings.language}
                    onChange={(e) =>
                        handleChange("language", e.target.value)
                    }
                >
                    <option value="English">English</option>
                </select>

                <label>Drawtime</label>
                <select
                    value={settings.drawtime}
                    onChange={(e) =>
                        handleChange("drawtime", Number(e.target.value))
                    }
                >
                    <option value={15}>15</option>
                    <option value={20}>20</option>
                    <option value={30}>30</option>
                    <option value={40}>40</option>
                    <option value={50}>50</option>
                    <option value={60}>60</option>
                    <option value={70}>70</option>
                    <option value={80}>80</option>
                    <option value={90}>90</option>
                    <option value={100}>100</option>
                    <option value={150}>150</option>
                    <option value={200}>200</option>
                    <option value={250}>250</option>
                </select>

                <label>Rounds</label>
                <select
                    value={settings.rounds}
                    onChange={(e) =>
                        handleChange("rounds", Number(e.target.value))
                    }
                >
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={4}>4</option>
                    <option value={5}>5</option>
                    <option value={6}>6</option>
                </select>

                <label>Word Count</label>
                <select
                    value={settings.wordCount}
                    onChange={(e) =>
                        handleChange("wordCount", Number(e.target.value))
                    }
                >
                    <option value={1}>1</option>
                    <option value={2}>2</option>
                    <option value={3}>3</option>
                    <option value={4}>4</option>
                    <option value={5}>5</option>
                </select>

                <label>Hints</label>
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
                    <option value={4}>4</option>
                    <option value={5}>5</option>
                </select>

            </div>

            <div className="custom-words">

                <div className="custom-word-header">
                    <div>Custom word</div>

                    <label>
                        Use custom words only
                        <input type="checkbox" />
                    </label>
                </div>

                <textarea
                    placeholder="Minimum of 10 words. 1-32 characters per word! 20000 characters maximum. Separated by a, (comma)"
                />

            </div>

            <div className="lobby-actions">

                <button
                    id="start"
                    onClick={() => onStart(settings)}
                >
                    Start!
                </button>

                <button id="invite">
                    invite
                </button>

            </div>

        </div>
    );
}

export default LobbySettings;