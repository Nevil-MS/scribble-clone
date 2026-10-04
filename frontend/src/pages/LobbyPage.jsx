import GameTitle from "../components/GameTitle"
import GameStatusBar from "../components/GameStatusBar"
import Chat from "../components/Chat"
import LobbySettings from "../components/LobbySettings"
import PlayerList from "../components/PlayerList"
import "./LobbyPage.css"

function LobbyPage() {
    return (
        <main>
            <div className="lobby-page">

                    <GameTitle />

                    <GameStatusBar />

                    <PlayerList />

                    <LobbySettings />

                    <Chat />

            </div>
             
        </main>
    )
}

export default LobbyPage