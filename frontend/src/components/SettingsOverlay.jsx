import KeyBindInput from "./KeybindInput.jsx"
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
                        <KeyBindInput label="Brush" defaultKey="B" />
                        <KeyBindInput label="Fill" defaultKey="F" />
                        <KeyBindInput label="Undo" defaultKey="U" />
                        <KeyBindInput label="Clear" defaultKey="C" />
                        <KeyBindInput label="Swap" defaultKey="S" />
                    </div>     
                </div>
                            
            </div>
        </div>
    )
}

export default SettingsOverlay