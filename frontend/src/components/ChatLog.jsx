import { useEffect } from "react";
import Message from "./Message";

function ChatLog({ messages, userTyping, loading, scrollToBottom }) {
  useEffect(() => {
    scrollToBottom();

    // eslint-disable-next-line
  }, [messages, userTyping, loading]);

  return (
    <>
      <div
        className={`chat-window overflow-auto mb-3 ${
          userTyping || loading ? "partial-chat" : "full-chat"
        }`}
      >
        <div id="chat-log">
          <div id="container message-container">
            {messages &&
              messages.map((message, index) => (
                <Message key={index} message={message} />
              ))}
          </div>
        </div>
      </div>
      <div
        className="chat-window typing-status"
        hidden={!userTyping && !loading}
      >
        {userTyping && (
          <div id="user-typing">
            <ul className="px-3">
              <li></li>
              <li></li>
              <li></li>
            </ul>
          </div>
        )}
        {loading && (
          <div id="assistant-typing">
            <ul className="px-3">
              <li></li>
              <li></li>
              <li></li>
            </ul>
          </div>
        )}
      </div>
    </>
  );
}

export default ChatLog;
