function Message({ message }) {
  return (
    <div className="row mx-2">
      {message && (message.role === "assistant" || message.role === "info") && (
        <div className="card chat-message message-assistant bg-secondary">
          <h5 className="card-body text-white lh-base">{message.content}</h5>
        </div>
      )}
      {message && message.role === "user" && (
        <div className="card chat-message message-user bg-primary">
          <h5 className="card-body text-white lh-base">{message.content}</h5>
        </div>
      )}
      {message && message.role === "image" && (
        <div className="card chat-message message-image bg-dark">
          <a href={message.content} rel="noreferrer" target="_blank">
            <img
              id={message.content.trim()}
              src={message.content}
              alt={message.content + "image"}
            />
          </a>
        </div>
      )}
    </div>
  );
}

export default Message;
