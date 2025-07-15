import * as React from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface TextInputProps {
  userTyping: boolean;
  setUserTyping: (typing: boolean) => void;
  handleKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  handleUserInputSubmit: (e?: React.FormEvent<HTMLFormElement>) => void;
  userInput: string;
  setUserInput: (val: string) => void;
  inputDisabled: boolean;
}

const TextInput: React.FC<TextInputProps> = ({
  userTyping,
  setUserTyping,
  handleKeyDown,
  handleUserInputSubmit,
  userInput,
  setUserInput,
  inputDisabled,
}) => {
  const onUserInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length === 0) {
      setUserTyping(false);
    } else if (!userTyping) {
      setUserTyping(true);
    }
    setUserInput(value);
  };

  return (
    <form
      id="user-input-form"
      className="flex space-x-2"
      onSubmit={(e) => {
        e.preventDefault();
        handleUserInputSubmit();
      }}
    >
      <Textarea
        id="user-input"
        name="user_input"
        placeholder="Type your message..."
        onKeyDown={handleKeyDown}
        onChange={onUserInputChange}
        value={userInput}
        disabled={inputDisabled}
        className="flex-1 resize-none"
      />
      <Button
        type="submit"
        disabled={inputDisabled || userInput.trim().length === 0}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M5 13l4 4L19 7"
          />
        </svg>
      </Button>
    </form>
  );
};

export default TextInput;
