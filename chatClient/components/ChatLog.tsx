import * as React from "react";
import Message, { MessageType } from "./Message";

interface ChatLogProps {
  messages: MessageType[];
  userTyping: boolean;
  loading: boolean;
  scrollToBottom: () => void;
}

const ChatLog: React.FC<ChatLogProps> = ({
  messages,
  userTyping,
  loading,
  scrollToBottom,
}) => {
  React.useEffect(() => {
    scrollToBottom();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, userTyping, loading]);

  return (
    <>
      <div
        className={`chat-window overflow-auto mb-3 ${
          userTyping || loading ? "h-[100px]" : "h-[300px]"
        }`}
      >
        <div id="chat-log" className="space-y-2 px-2">
          {messages.map((message, index) => (
            <Message key={index} message={message} />
          ))}
        </div>
      </div>
      <div
        className="chat-window typing-status"
        hidden={!userTyping && !loading}
      >
        {userTyping && (
          <div id="user-typing" className="flex items-center px-3">
            <div className="h-2 w-2 animate-ping rounded-full bg-blue-500 mr-1" />
            <div className="h-2 w-2 animate-ping rounded-full bg-blue-500 mr-1" />
            <div className="h-2 w-2 animate-ping rounded-full bg-blue-500" />
          </div>
        )}
        {loading && (
          <div id="assistant-typing" className="flex items-center px-3">
            <div className="h-2 w-2 animate-ping rounded-full bg-gray-500 mr-1" />
            <div className="h-2 w-2 animate-ping rounded-full bg-gray-500 mr-1" />
            <div className="h-2 w-2 animate-ping rounded-full bg-gray-500" />
          </div>
        )}
      </div>
    </>
  );
};

export default ChatLog;
