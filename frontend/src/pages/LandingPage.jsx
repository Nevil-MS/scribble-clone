import GameTitle from "../components/GameTitle"
import "./LandingPage.css"

function LandingPage() {
    return (
        <main>
            <GameTitle />

            <div className="player-setup">
                <div className="name-lang">
                    <input placeholder="Enter your name" />

                    <select defaultValue="en">
                        <option value="en">English</option>
                    </select>
                </div>

                <div className="avatar-setup">
                    <button value="prev">prev</button>

                    <div className="avatar-placeholder">Avatar</div>

                    <button value="next">next</button>
                </div>

                <button>Play!</button>
            </div>
        </main>

    )
}

export default LandingPage