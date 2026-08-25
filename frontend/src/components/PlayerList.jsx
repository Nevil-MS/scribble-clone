import "./PlayerList.css"

function PlayerList() {
    return (
            <div className="player-list">
                <div className="player-info">
                    <div className="player-position">#1</div>
                    <div className="player-name">Player 1</div>
                    <div className="player-points">0 points</div>
                    <div className="player-avatar">avatar</div>
                </div>
                <div className="player-info">
                    <div className="player-position">#1</div>
                    <div className="player-name">Player 2</div>
                    <div className="player-points">0 points</div>
                    <div className="player-avatar">avatar</div>
                </div>
                <div className="player-info">
                    <div className="player-position">#1</div>
                    <div className="player-name">Player 2</div>
                    <div className="player-points">0 points</div>
                    <div className="player-avatar">avatar</div>
                </div>
            </div>
    )
}

export default PlayerList