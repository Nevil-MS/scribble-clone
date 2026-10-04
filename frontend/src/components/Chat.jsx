import { useState } from "react";
import "./styles/Chat.css";

const defaultMessages = [
  { id: 1, player: "Player 1", text: "Hello!" },
  { id: 2, player: "Player 2", text: "Hi!" },
];

function Chat({
  messages = defaultMessages,
  onSendMessage = () => {},
}) {
  const [message, setMessage] = useState("");

  function handleSubmit(e) {
    e.preventDefault();

    const trimmedMessage = message.trim();

    if (!trimmedMessage) {
      return;
    }

    onSendMessage(trimmedMessage);
    setMessage("");
  }

  return (
    <div className="chat">
      <div className="chat-message">
        {messages.map((msg) => (
          <div className="message" key={msg.id}>
            {msg.player}: {msg.text}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Type your guess here..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
      </form>
    </div>
  );
}

export default Chat;