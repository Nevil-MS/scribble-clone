import GameTitle from "../components/GameTitle"
import GameStatusBar from "../components/GameStatusBar"
import Chat from "../components/Chat"
import PlayerList from "../components/PlayerList"
import "./LobbyPage.css"

function LobbyPage() {
    return (
        <main>
            <div className="lobby-page">

                <GameTitle />


                <GameStatusBar />

                <div className="lobby-info">
                    {/*lobby-info has three children player-list, lobby-settings, chat*/} 

                    <PlayerList />

                     
                    <div className="game-settings">
                        <div className="lobby-settings"> 
                            <div className="setting-row">
                                <label>Players</label>
                                <select defaultValue={2}>
                                    <option value={2}>2</option>
                                    <option value={3}>3</option>
                                    <option value={4}>4</option>
                                    <option value={5}>5</option>
                                    <option value={6}>6</option>
                                </select>
                            </div>

                            <div className="setting-row">
                                <label>Language</label>
                                <select defaultValue="en">
                                    <option value="en">English</option>
                                </select>
                            </div>

                            <div className="setting-row">
                                <label>Drawtime</label>
                                <select defaultValue={80}>
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
                            </div>

                            <div className="setting-row">
                                <label>Rounds</label>
                                <select defaultValue={3}>
                                    <option value={2}>2</option>
                                    <option value={3}>3</option>
                                    <option value={4}>4</option>
                                    <option value={5}>5</option>
                                    <option value={6}>6</option>
                                </select>
                            </div>
                                
                            <div className="setting-row">
                                <label>Word Count</label>
                                <select defaultValue={3}>
                                    <option value={1}>1</option>
                                    <option value={2}>2</option>
                                    <option value={3}>3</option>
                                    <option value={4}>4</option>
                                    <option value={5}>5</option>
                                </select>
                            </div>
                                
                            <div className="setting-row">
                                <label>Hints</label>
                                <select defaultValue={2}>
                                    <option value={0}>0</option>
                                    <option value={1}>1</option>
                                    <option value={2}>2</option>
                                    <option value={3}>3</option>
                                    <option value={4}>4</option>
                                    <option value={5}>5</option>
                                </select>
                            </div>

                            <div className="custom-word-header">
                                <div>Custom word</div>

                                <label>
                                    Use custom words only
                                    <input type="checkbox" />
                                </label>
                            </div>

                            <textarea placeholder="Minimum of 10 words. 1-32 characters per word! 20000 characters maximum. Separated by a, (comma)" />

                            <div className="lobby-actions">
                                <button id="start">Start!</button>
                                <button id="invite">invite</button>
                            </div>
                        </div>
                    </div>

                    <Chat />

                </div>
            </div>

                
        </main>
    )
}

export default LobbyPage