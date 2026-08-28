import "./styles/GameStatusBar.css"

function GameStatusBar(){
    return(
        <div className="game-status-bar">
            <div className="left-info">
                <div className="clock">OO</div>

                <div className="round-info">Round 1 of 3</div>
            </div>
            
            <div className="game-status">waiting</div>

            <button>Settings</button>
        </div>
    )
}

export default GameStatusBar