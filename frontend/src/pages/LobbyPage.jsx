import { useEffect, useRef, useState } from "react";
import { connectGameSocket } from "../network/gameSocket";
import GameTitle from "../components/GameTitle";
import GameStatusBar from "../components/GameStatusBar";
import Chat from "../components/Chat";
import LobbySettings from "../components/LobbySettings";
import PlayerList from "../components/PlayerList";
import "./LobbyPage.css";

function LobbyPage({ roomId, playerName, pid, onGameStart }) {
    const [players, setPlayers] = useState([]);
    const [messages, setMessages] = useState([]);
    const pidRef = useRef(null);
    const socketRef = useRef(null);
    const pendingSettingsRef = useRef(null);

    useEffect(() => {
        if (!roomId) {
            return;
        }

        const connection = connectGameSocket({
            roomId,
            pid,

            onOpen: () => {
                console.log("Lobby WebSocket connected:", roomId);
            },

            onMessage: (message) => {
                console.log("Lobby received:", message);

                if (message.type === "connection") {
                    pidRef.current = message.data.pid;

                    console.log(
                        "Lobby PID:",
                        pidRef.current
                    );

                    connection.send("join", {
                        name: playerName,
                        avatar: "avatar_01",
                    });

                    return;
                }

                if (message.type === "game_state") {
                    const data = message.data;
                    if (data.players) {
    setPlayers(
        data.players.map((player) => ({
            id: player.pid,
            name: player.name,
            points: player.points ?? 0,
            initials: player.name
                .slice(0, 2)
                .toUpperCase(),
            avatar: player.avatar,
        }))
    );
}

                    console.log(
                        "Lobby game state:",
                        data.state
                    );

                    /*
                     * Stay on LobbyPage while the backend
                     * says LOBBY.
                     *
                     * Only leave when the backend actually
                     * advances the game.
                     */
                    if (
                        data.state &&
                        data.state !== "LOBBY"
                    ) {
                        console.log(
                            "Game actually started:",
                            data.state
                        );

                        onGameStart(
                            pendingSettingsRef.current,
                            pidRef.current
                        );
                    }

                    return;
                }
                if (message.type === "chat") {
    const chatMessage = message.data;

    setMessages((previous) => [
        ...previous,
        {
            id: `${Date.now()}-${chatMessage.pid}`,
            player: chatMessage.name,
            text: chatMessage.message,
        },
    ]);

    return;
}

if (message.type === "system_message") {
    setMessages((previous) => [
        ...previous,
        {
            id: `${Date.now()}-system`,
            player: "System",
            text: message.data.message,
        },
    ]);

    return;
}

                if (message.type === "error") {
                    console.error(
                        "Backend error:",
                        message.data.message
                    );

                    /*
                     * IMPORTANT:
                     * We do NOT navigate anywhere on error.
                     * The user stays in the existing lobby.
                     */
                    return;
                }

                if (message.type === "player_joined") {
                    console.log(
                        "Player joined:",
                        message.data.player
                    );

                    return;
                }

                if (message.type === "player_left") {
                    console.log(
                        "Player left:",
                        message.data.pid
                    );
                }
            },

            onClose: () => {
                console.log("Lobby WebSocket closed.");
            },

            onError: (error) => {
                console.error(
                    "Lobby WebSocket error:",
                    error
                );
            },
        });

        socketRef.current = connection;

        return () => {
            connection?.close();
            socketRef.current = null;
        };
    }, [roomId, playerName, onGameStart]);

function handleSendMessage(text) {
    if (!text.trim()) {
        return;
    }

    socketRef.current?.send("chat", {
        message: text,
    });
}


    function handleStart(settings) {
        console.log("Lobby settings:", settings);

        const connection = socketRef.current;

        if (!connection) {
            console.error(
                "Cannot start: lobby WebSocket is not connected."
            );
            return;
        }

        /*
         * Remember the settings in case the backend
         * confirms that the game actually started.
         */
        pendingSettingsRef.current = settings;

        /*
         * Translate frontend setting names into the
         * backend's expected format.
         */
        connection.send("lobby_update", {
            player_count: settings.players,
            language: settings.language,
            draw_time: settings.drawtime,
            rounds: settings.rounds,
            word_count: settings.wordCount,
            hints: settings.hints,
            custom_words: [],
            custom_words_only: false,
        });

        /*
         * Ask the backend to start.
         *
         * We DO NOT navigate here.
         */
        connection.send("start_game");
    }

    return (
        <main>
            <div className="lobby-page">
                <GameTitle />

                <GameStatusBar />

                <PlayerList players={players} />

                <LobbySettings
                    onStart={handleStart}
                />

                <Chat
                    messages={messages}
                    onSendMessage={handleSendMessage}
                />
            </div>
        </main>
    );
}

export default LobbyPage;