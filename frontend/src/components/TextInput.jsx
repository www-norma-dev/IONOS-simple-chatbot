function TextInput({
  userTyping,
  setUserTyping,
  error,
  setError,
  handleKeyDown,
  handleUserInputSubmit,
  userInput,
  setUserInput,
  inputDisabled,
}) {
  const onUserInputChange = (e) => {
    if (e.target.value.length === 0) {
      setUserTyping(false);
    } else if (!userTyping) {
      setUserTyping(true);
      setError(false);
    }
    setUserInput(e.target.value);
  };

  return (
    <>
      <form id="user-input-form" className="position-relative">
        {error && <h5 className="tooltip">Please enter a prompt.</h5>}
        <div id="chat-input">
          <textarea
            id="user-input"
            name="user_input"
            className="form-control"
            placeholder="Type message"
            onKeyDown={handleKeyDown}
            onChange={onUserInputChange}
            value={userInput}
            disabled={inputDisabled}
          />
          <button
            id="chat-input-button"
            className="btn btn-primary rounded-4"
            type="submit"
            disabled={inputDisabled}
            onClick={(e) => handleUserInputSubmit(e)}
          >
            <span className="material-symbols-outlined">send</span>
          </button>
        </div>
      </form>
    </>
  );
}

export default TextInput;
