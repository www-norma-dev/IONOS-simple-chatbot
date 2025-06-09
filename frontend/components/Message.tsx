import * as React from "react";
import ReactMarkdown from "react-markdown";

const Message: React.FC<any> = ({ message }) => {
  const baseClasses = "my-1 px-4 py-2 rounded-lg max-w-[75%] break-words";

  if (message.role === "assistant" || message.role === "info") {
    return (
      <div className="flex justify-start">
        <div className={`${baseClasses} bg-gray-200 text-gray-900`}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    );
  }

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className={`${baseClasses} bg-blue-600 text-white`}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    );
  }

  if (message.role === "image") {
    return (
      <div className="flex justify-center my-2">
        <a href={message.content} target="_blank" rel="noreferrer">
          <img
            className="rounded-lg border border-gray-300 max-h-60"
            src={message.content}
            alt="Generated"
          />
        </a>
      </div>
    );
  }

  return null;
};

export default Message;
