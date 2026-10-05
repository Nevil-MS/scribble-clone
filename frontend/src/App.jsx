import { useState } from "react";
import LandingPage from "./pages/LandingPage";
import LobbyPage from "./pages/LobbyPage";
import GamePage from "./pages/GamePage";

function App() {
  const [page, setPage] = useState("landing");
  const [gameSettings, setGameSettings] = useState(null);

  if (page === "landing") {
    return <LandingPage onPlay={() => setPage("lobby")} />;
  }

  if (page === "lobby") {
    return (
      <LobbyPage
        onStart={(settings) => {
          setGameSettings(settings);
          setPage("game");
        }}
      />
    );
  }

  return <GamePage settings={gameSettings} />;
}

export default App;