import { useEffect, useState } from "react";

import ChatLog from "../components/ChatLog";
import TextInput from "../components/TextInput";
import ApiKeyModal from "../components/ApiKeyModal";

const MODEL_OPTIONS = [
  {
    label: "meta-llama-3-1-405b-instruct-fp8",
    value: "0b6c4a15-bb8d-4092-82b0-f357b77c59fd",
  },
  {
    label: "meta-llama-3-3-70b-instruct",
    value: "b18b18de-92c3-466e-81a8-e5df91890091",
  },
  {
    label: "flux-1-schnell",
    value: "6cbc28c9-217d-421c-85fb-754d79c61423",
  },
  {
    label: "meta-llama-3-8b-instruct",
    value: "2ba0c784-2e6a-4509-b3dd-cbd66cf0a75f",
  },
  {
    label: "mistral-7b-instruct",
    value: "053fd9b8-a73d-427d-9b21-7499d94dba42",
  },

  // add more models here…
];

function Home() {
  const baseURL = process.env.REACT_APP_BASE_URL ?? "http://localhost:8000";

  // model selection & activation
  const [selectedModel, setSelectedModel] = useState("");
  const [chatEnabled, setChatEnabled] = useState(false);

  // auth & chat states
  const [apiKeyError, setApiKeyError] = useState(false);
  const [error, setError] = useState(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState(false);
  const [apiKey, setApiKey] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userTyping, setUserTyping] = useState(false);
  const [inputDisabled, setInputDisabled] = useState(false);
  const [userInput, setUserInput] = useState("");

  // scroll helper
  const scrollToBottom = () => {
    const chatWindow = document.querySelector("#chat-log")?.parentElement;
    chatWindow?.scrollTo(0, chatWindow.scrollHeight);
  };

  // cookie helpers
  const getCookie = () =>
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("chatbot_apikey="))
      ?.split("=");
  const resetCookie = () => {
    const c = getCookie();
    if (c) document.cookie = `${c[0]}=;expires=Thu, 01 Jan 1970 00:00:00 UTC`;
  };

  // fetch chat log
  const fetchMessages = async () => {
    try {
      const res = await fetch(`${baseURL}/`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey,
          "x-model-id": selectedModel,
        },
      });
      const data = await res.json();
      setMessages(data);
      setTimeout(scrollToBottom, 100);
    } catch (e) {
      console.error("Fetch error:", e);
    }
  };

  // on mount: check API key cookie
  useEffect(() => {
    const c = getCookie();
    if (c && c[1]) {
      setApiKey(c[1]);
    } else {
      setShowApiKeyModal(true);
    }
  }, []);

  // enable chat and load history
  const handleStartChat = () => {
    if (!selectedModel) return;
    setChatEnabled(true);
    fetchMessages();
  };

  // send user message
  const handleUserInputSubmit = async (e) => {
    e?.preventDefault();
    if (!userInput.trim() || !chatEnabled) return;

    setInputDisabled(true);
    setUserTyping(false);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: userInput }]);
    setUserInput("");

    try {
      const isImage = userInput.toLowerCase().startsWith("/image ");
      await fetch(`${baseURL}/${isImage ? "i" : ""}`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "x-api-key": apiKey,
          "x-model-id": selectedModel,
        },
        body: JSON.stringify({ prompt: userInput }),
      });
      await fetchMessages();
    } catch (e) {
      console.error("Send error:", e);
    } finally {
      setLoading(false);
      setInputDisabled(false);
    }
  };

  // reset chat history
  const onResetClick = async () => {
    setInputDisabled(true);
    try {
      const res = await fetch(`${baseURL}/`, {
        method: "DELETE",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "x-api-key": apiKey,
          "x-model-id": selectedModel,
        },
      });
      const data = await res.json();
      setMessages(data);
    } catch (e) {
      console.error("Reset error:", e);
    } finally {
      setInputDisabled(false);
    }
  };

  // render API key modal
  if (showApiKeyModal) {
    return (
      <ApiKeyModal
        show={showApiKeyModal}
        setShow={setShowApiKeyModal}
        apiKeyError={apiKeyError}
        handleAPIKeyModalClick={() => {
          const inp = document.getElementById("apiKeyForm.input");
          if (inp.value) {
            document.cookie = `chatbot_apikey=${inp.value}; SameSite=None; Secure`;
            setApiKey(inp.value);
            setApiKeyError(false);
            setShowApiKeyModal(false);
          } else {
            setApiKeyError(true);
          }
        }}
      />
    );
  }

  return (
    <>
      <div className="container">
        {/* left panel: model selector */}
        <div className="sidebar">
          <label htmlFor="modelSelect" className="form-label">
            Choose Model
          </label>
          <select
            id="modelSelect"
            className="form-select mb-2"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            <option value="">-- Select a model --</option>
            {MODEL_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            className="btn btn-primary"
            onClick={handleStartChat}
            disabled={!selectedModel}
          >
            Start Chat
          </button>
        </div>

        {/* right panel: chat */}
        <div className="chat-panel">
          <div id="header">
            <h3 className="font-roboto-bold">Personal Chatbot</h3>
            {chatEnabled && messages.length > 2 && (
              <button
                id="chat-reset"
                className="btn btn-warning"
                onClick={onResetClick}
                disabled={inputDisabled}
              >
                Reset Chat Log
              </button>
            )}
          </div>

          <hr />

          <div className="row">
            <ChatLog
              messages={messages}
              userTyping={userTyping}
              loading={loading}
              scrollToBottom={scrollToBottom}
            />

            <TextInput
              userTyping={userTyping}
              setUserTyping={setUserTyping}
              error={error}
              setError={setError}
              handleKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleUserInputSubmit();
                }
              }}
              handleUserInputSubmit={handleUserInputSubmit}
              userInput={userInput}
              setUserInput={setUserInput}
              inputDisabled={inputDisabled || !chatEnabled}
            />
          </div>
        </div>
      </div>
    </>
  );
}

export default Home;
