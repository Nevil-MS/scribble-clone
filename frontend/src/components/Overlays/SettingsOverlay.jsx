import KeybindInput from "../KeybindInput.jsx"
import "./SettingsOverlay.css"

function SettingsOverlay() {
    return(
        <div className="settings-overlay">
            <div className="settings">
                <button className="close-button">X</button>

                <div className="setting-title"><h2>Settings</h2></div>

                <div className="volume-setting">
                    <div>Volume</div>
                    <div className="volume-controls">
                        <button value="-">-</button>
                        <div>100</div>
                        <button value="+">+</button>
                    </div>
                </div>

                <div className="hotkey-settings">
                    <div className="hotkey-reset">
                        <div>Hotkeys</div>
                        <button value={0}>reset</button>
                    </div>
                    
                    <div className="key-bindings">
                        <KeybindInput label="Brush" defaultKey="B" />
                        <KeybindInput label="Fill" defaultKey="F" />
                        <KeybindInput label="Undo" defaultKey="U" />
                        <KeybindInput label="Clear" defaultKey="C" />
                        <KeybindInput label="Swap" defaultKey="S" />
                    </div>     
                </div>
                            
            </div>
        </div>
    )
}

export default SettingsOverlay