import GameTitle from "../components/GameTitle"
import GameStatusBar from "../components/GameStatusBar"
import Chat from "../components/Chat"
import LobbySettings from "../components/LobbySettings"
import PlayerList from "../components/PlayerList"
import "./LobbyPage.css"

function LobbyPage({ onStart }) {
    return (
        <main>
            <div className="lobby-page">

                    <GameTitle />

                    <GameStatusBar />

                    <PlayerList />

                    <LobbySettings onStart={onStart} />

                    <Chat />

            </div>
             
        </main>
    )
}

export default LobbyPage