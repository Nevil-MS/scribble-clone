import { useEffect, useRef, useState } from "react";
import "./RoundOverlay.css";

function RoundOverlay({ round, totalRounds, player, onComplete }) {
  const [countdown, setCountdown] = useState(3);
  const completedRef = useRef(false);

  // Reset countdown when a new round starts
  useEffect(() => {
    setCountdown(3);
    completedRef.current = false;
  }, [round]);

  // Countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((previous) => {
        if (previous <= 1) {
          clearInterval(timer);
          return 0;
        }

        return previous - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [round]);

  // Complete the round after countdown reaches 0
  useEffect(() => {
    if (countdown === 0 && !completedRef.current) {
      completedRef.current = true;
      onComplete();
    }
  }, [countdown, onComplete]);

  return (
    <div className="canvas-overlay round-overlay">
      <h1>Round {round}</h1>
      <p>{player} is drawing</p>

      <div className="round-countdown">{countdown}</div>
    </div>
  );
}

export default RoundOverlay;