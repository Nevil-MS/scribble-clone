import { useEffect, useState } from "react";
import "./RoundOverlay.css";

function RoundOverlay({ round, totalRounds, player, onComplete }) {
  const [countdown, setCountdown] = useState(3);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((previous) => {
        if (previous <= 1) {
          clearInterval(timer);
          onComplete();
          return 0;
        }

        return previous - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [onComplete]);

  return (
    <div className="canvas-overlay round-overlay">
      <h1>Round {round}</h1>
      <p>{player} is drawing</p>

      <div className="round-countdown">{countdown}</div>
    </div>
  );
}

export default RoundOverlay;