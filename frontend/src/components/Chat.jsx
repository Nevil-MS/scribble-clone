import "./styles/Chat.css"

function Chat() {
    return(
            <div className="chat">
                <div className="chat-message">
                    <div className="message">Player 1: Hello!</div>
                    <div className="message">Player 2: Hi!</div>
                </div>
                    
                <input type="text" placeholder="Type your guess here..." />
            </div>
    )
}

export default Chat