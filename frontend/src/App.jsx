import { useState } from "react";
import LandingPage from "./pages/LandingPage";
import LobbyPage from "./pages/LobbyPage";
import GamePage from "./pages/GamePage";

function App() {
    const [page, setPage] = useState("landing");
    const [playerName, setPlayerName] = useState("");
    const [roomId, setRoomId] = useState("");
    const [gameSettings, setGameSettings] = useState(null);
    const [playerPid, setPlayerPid] = useState(null);

    async function createRoom(name) {
        try {
            const response = await fetch("/rooms", {
                method: "POST",
            });

            if (!response.ok) {
                throw new Error(
                    "Failed to create room"
                );
            }

            const data = await response.json();

            console.log(
                "Room created:",
                data.room_id
            );

            setPlayerName(name);
            setRoomId(data.room_id);
            setPage("lobby");
        } catch (error) {
            console.error(
                "Room creation failed:",
                error
            );

            alert(
                "Could not create room. Is the backend running?"
            );
        }
    }

    function handleGameStart(settings, pid) {
        console.log(
            "Backend confirmed game start:",
            settings
        );

        console.log(
            "Player PID:",
            pid
        );

        setGameSettings(settings);
        setPlayerPid(pid);
        setPage("game");
    }

    if (page === "landing") {
        return (
            <LandingPage
                onPlay={(name) => {
                    createRoom(name);
                }}
            />
        );
    }

    if (page === "lobby") {
        return (
            <LobbyPage
                roomId={roomId}
                playerName={playerName}
                onGameStart={handleGameStart}
            />
        );
    }

    return (
        <GamePage
            settings={gameSettings}
            playerName={playerName}
            roomId={roomId}
            pid={playerPid}
        />
    );
}

export default App;