const BACKEND_URL =
  import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

const WS_URL = BACKEND_URL.replace(/^http/, "ws");

/**
 * Frontend ↔ Backend WebSocket interface.
 *
 * The networking implementation can change internally,
 * but GamePage/LobbyPage should only depend on this API.
 */
export function connectGameSocket({
  roomId,
  pid,
  onMessage,
  onOpen,
  onClose,
  onError,
}) {
  if (!roomId) {
    console.error("Cannot connect: no roomId provided.");
    return null;
  }

  const url = pid
    ? `${WS_URL}/ws/${roomId}?pid=${encodeURIComponent(pid)}`
    : `${WS_URL}/ws/${roomId}`;

  const socket = new WebSocket(url);

  socket.onopen = () => {
    console.log("WebSocket connected:", roomId);
    onOpen?.();
  };

  socket.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);

      console.log("Server → Frontend:", message);

      onMessage?.(message);
    } catch (error) {
      console.error("Invalid server message:", event.data);
    }
  };

  socket.onerror = (error) => {
    console.error("WebSocket error:", error);
    onError?.(error);
  };

  socket.onclose = () => {
    console.log("WebSocket disconnected");
    onClose?.();
  };

  /**
   * Send a message to the backend.
   *
   * Example:
   * send("chat", { message: "hello" });
   */
  function send(type, data = {}) {
    if (socket.readyState !== WebSocket.OPEN) {
      console.warn("WebSocket is not connected.");
      return false;
    }

    socket.send(
      JSON.stringify({
        type,
        data,
      })
    );

    return true;
  }

  /**
   * Close the current WebSocket connection.
   */
  function close() {
    if (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    ) {
      socket.close();
    }
  }

  return {
    socket,
    send,
    close,
  };
}