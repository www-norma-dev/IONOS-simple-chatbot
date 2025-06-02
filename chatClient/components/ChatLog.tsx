// ChatLog.tsx
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
      {/* This div grows to fill remaining vertical space and scrolls */}
      <div className="flex-1 overflow-auto mb-3">
        <div id="chat-log" className="space-y-2 px-2">
          {messages.map((message, index) => (
            <Message key={index} message={message} />
          ))}
        </div>
      </div>

      {/* 
        When `loading` is true (assistant is “typing”), show gray dots aligned left.
      */}
      {loading && (
        <div className="flex w-full px-3 py-1">
          {/* left‐justify */}
          <div id="assistant-typing" className="flex items-center space-x-1">
            <div className="h-2 w-2 animate-ping rounded-full bg-gray-500" />
            <div className="h-2 w-2 animate-ping rounded-full bg-gray-500" />
            <div className="h-2 w-2 animate-ping rounded-full bg-gray-500" />
          </div>
        </div>
      )}

      {/*
        When `userTyping` is true, show blue dots aligned right.
      */}
      {userTyping && (
        <div className="flex w-full px-3 py-1 justify-end">
          <div id="user-typing" className="flex items-center space-x-1">
            <div className="h-2 w-2 animate-ping rounded-full bg-blue-500" />
            <div className="h-2 w-2 animate-ping rounded-full bg-blue-500" />
            <div className="h-2 w-2 animate-ping rounded-full bg-blue-500" />
          </div>
        </div>
      )}
    </>
  );
};

export default ChatLog;
