import { useEffect, useRef, useState } from "react";

import { connectGameSocket } from "../network/gameSocket";

import GameTitle from "../components/GameTitle";

import PointsOverlay from "../components/Overlays/PointsOverlay";

import GameStatusBar from "../components/GameStatusBar";

import LobbyOverlay from "../components/LobbyOverlay";

import PlayerList from "../components/PlayerList";

import Chat from "../components/Chat";

import CanvasToolbar from "../components/CanvasToolbar";

import ChoiceOverlay from "../components/Overlays/ChoiceOverlay";

import WaitingOverlay from "../components/Overlays/WaitingOverlay";

import DrawingCanvas from "../components/DrawingCanvas";

import Leaderboard from "../components/Leaderboard";

import "./GamePage.css";

function GamePage({ playerName, roomId, pid }) {
  const canvasRef = useRef(null);

  const socketRef = useRef(null);

  const pidRef = useRef(null);

  /*
   * This is now controlled by the backend.
   *
   * lobby
   * waiting
   * choosing
   * drawing
   * points
   * leaderboard
   */
  const [gameState, setGameState] = useState("lobby");

  const [tool, setTool] = useState("pencil");

  const [color, setColor] = useState("#000000");

  const [size, setSize] = useState(7);

  const [players, setPlayers] = useState([]);

  const [round, setRound] = useState(1);

  const [totalRounds, setTotalRounds] = useState(3);

  const [gameStatus, setGameStatus] = useState("Waiting for players...");

  const [timeRemaining, setTimeRemaining] = useState(null);

  const [messages, setMessages] = useState([]);

  const [wordOptions, setWordOptions] = useState([]);

  const [word, setWord] = useState(null);

  const [wordPattern, setWordPattern] = useState(null);

  const [isDrawer, setIsDrawer] = useState(false);

  /*
   * Convert backend game states into the existing UI states.
   */
  function applyBackendGameState(data) {
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

    if (data.settings) {
      setTotalRounds(data.settings.rounds);
    }

    if (data.current_round !== null && data.current_round !== undefined) {
      setRound(data.current_round);
    }

    if (data.word !== undefined) {
      setWord(data.word);
    }

    if (data.state) {
      switch (data.state) {
        case "LOBBY":
          setGameState("lobby");
          setGameStatus("Waiting for players...");
          setTimeRemaining(null);
          break;

        case "ROUND_START":
          setGameState("waiting");
          setGameStatus("Round starting...");
          break;

        case "TURN_START":
          setGameState("waiting");
          setGameStatus("Turn starting...");
          break;

        case "WORD_SELECTION":
          setGameState("choosing");
          setGameStatus("Choose a word");
          break;

        case "PLAYING":
          setGameState("drawing");
          setGameStatus(
            isDrawer ? "You are drawing" : "Player is drawing"
          );
          break;

        case "TURN_END":
          setGameState("points");
          setGameStatus("Round complete");
          setTimeRemaining(null);
          break;

        case "ROUND_END":
          setGameState("points");
          setGameStatus("Round complete");
          setTimeRemaining(null);
          break;

        case "GAME_END":
          setGameState("leaderboard");
          setGameStatus("Game complete");
          setTimeRemaining(null);
          break;

        default:
          console.log("Unhandled backend state:", data.state);
      }
    }
  }

  /*
   * WebSocket connection
   */
  useEffect(() => {
    if (!roomId) {
      return;
    }

    const connection = connectGameSocket({
      roomId,
      pid,

      onOpen: () => {
        console.log("Connected to game room:", roomId);
      },

      onMessage: (message) => {
        console.log("Received from server:", message);

        /*
         * Backend gives us our PID immediately after connecting.
         */
        if (message.type === "connection") {
          pidRef.current = message.data.pid;

          console.log(
            "Connected with PID:",
            message.data.pid
          );

          connection.send("join", {
            name: playerName,
            avatar: "default",
          });

          return;
        }

        /*
         * Main game state.
         */
        if (message.type === "game_state") {
          const data = message.data;

          console.log("Game state:", data);

          /*
           * Special word events don't necessarily contain
           * a normal `state` field.
           */
          if (data.event === "word_selected") {
            setWord(data.word);
            setWordPattern(data.pattern);
            setIsDrawer(Boolean(data.is_drawer));

            setGameState("drawing");
            setGameStatus(
              data.is_drawer
                ? "You are drawing"
                : "Player is drawing"
            );

            return;
          }

          if (data.event === "word_visibility") {
            setWord(data.word);
            setWordPattern(data.pattern);
            setIsDrawer(Boolean(data.is_drawer));

            return;
          }

          applyBackendGameState(data);
          return;
        }

        /*
         * Backend sends word choices only to the drawer.
         */
        if (message.type === "word_options") {
          setWordOptions(message.data.options ?? []);
          setGameState("choosing");
          setGameStatus("Choose a word");
          return;
        }

        /*
         * Backend timer.
         */
        if (message.type === "timer") {
          setTimeRemaining(message.data.seconds);

          if (message.data.phase === "drawing") {
            setGameState("drawing");
          }

          return;
        }

        /*
         * Player joined.
         *
         * A game_state normally follows this, so the player
         * list itself is updated from game_state.
         */
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

          return;
        }

        /*
         * Chat.
         */
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

        /*
         * System messages.
         */
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

        /*
         * Final leaderboard.
         */
        if (message.type === "leaderboard") {
          console.log(
            "Leaderboard:",
            message.data.players
          );

          setGameState("leaderboard");
          setGameStatus("Game complete");

          return;
        }

        if (message.type === "error") {
          console.error(
            "Backend error:",
            message.data.message
          );

          return;
        }
      },

      onClose: () => {
        console.log("Game connection closed.");
      },

      onError: (error) => {
        console.error(
          "Game connection error:",
          error
        );
      },
    });

    socketRef.current = connection;

    return () => {
      connection?.close();
      socketRef.current = null;
    };
  }, [roomId, playerName, pid]);

  /*
   * Lobby start.
   *
   * First update the backend settings,
   * then tell the backend to start the game.
   */
  function handleLobbyStart(settings) {
    console.log("Lobby settings:", settings);

    const connection = socketRef.current;

    if (!connection) {
      console.error("No WebSocket connection.");
      return;
    }

    connection.send("lobby_update", {
      player_count: settings.players,
      language: settings.language,
      draw_time: settings.drawtime,
      rounds: settings.rounds,
      word_count: settings.wordCount,
      hints: settings.hints,
      custom_words: settings.customWords
        ? settings.customWords
            .split(",")
            .map((word) => word.trim())
            .filter(Boolean)
        : [],
      custom_words_only: settings.customWordsOnly,
    });

    connection.send("start_game");
  }

  /*
   * Word selection.
   */
  function handleWordChoice(option) {
    console.log("Word selected:", option);

    socketRef.current?.send("select_word", {
      word_id: option.word_id,
    });

    setWordOptions([]);
  }

  /*
   * Chat.
   */
  function handleSendMessage(text) {
    if (!text.trim()) {
      return;
    }

    socketRef.current?.send("chat", {
      message: text,
    });
  }

  /*
   * Drawing.
   */
  function handleStroke(stroke) {
    socketRef.current?.send("draw", stroke);
  }

  return (
    <main>
      <div className="game-page">

        <GameTitle />

        <GameStatusBar
          round={round}
          totalRounds={totalRounds}
          status={gameStatus}
          timeRemaining={timeRemaining}
        />

        <div className="game-content">

          <PlayerList players={players} />

          <div className="canvas-column">

            <div className="canvas-section">

              <DrawingCanvas
                ref={canvasRef}
                round={round}
                color={color}
                size={size}
                tool={tool}

                onStroke={handleStroke}

                onUndo={() => {
                  console.log("Undo");
                }}

                onClear={() => {
                  console.log("Clear");
                }}
              />

              {gameState === "lobby" && (
                <LobbyOverlay
                  onStart={handleLobbyStart}
                />
              )}

              {gameState === "waiting" && (
                <WaitingOverlay />
              )}

              {gameState === "choosing" && (
                <ChoiceOverlay
                  options={wordOptions}
                  onChoose={handleWordChoice}
                />
              )}

              {gameState === "points" && (
                <PointsOverlay />
              )}

              {gameState === "leaderboard" && (
                <Leaderboard />
              )}

            </div>

            <CanvasToolbar
              hidden={gameState !== "drawing"}
              tool={tool}
              setTool={setTool}
              color={color}
              setColor={setColor}
              size={size}
              setSize={setSize}
              onUndo={() => canvasRef.current?.undo()}
              onClear={() => canvasRef.current?.clearCanvas()}
            />

          </div>

          <Chat
            messages={messages}
            onSendMessage={handleSendMessage}
          />

        </div>
      </div>
    </main>
  );
}

export default GamePage;