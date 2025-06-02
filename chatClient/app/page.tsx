// src/pages/Home.tsx
"use client";
import * as React from "react";
import ChatLog from "@/components/ChatLog";
import TextInput from "@/components/TextInput";
import ApiKeyModal from "@/components/ApiKeyModal";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { MessageType } from "@/components/Message";

interface ModelOption {
  label: string;
  value: string;
}

const MODEL_OPTIONS: ModelOption[] = [
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

const Home: React.FC = () => {
  const baseURL =
    process.env.NEXT_PUBLIC_APP_BASE_URL ?? "http://localhost:8000";

  // Model & UI state
  const [pageUrl, setPageUrl] = React.useState<string>(""); // URL to scrape
  const [selectedModel, setSelectedModel] = React.useState<string>(""); // chosen model ID
  const [chatEnabled, setChatEnabled] = React.useState<boolean>(false); // when true, show chat UI

  // Auth & chat states
  const [apiKeyError, setApiKeyError] = React.useState<boolean>(false);
  const [error, setError] = React.useState<boolean>(false);
  const [showApiKeyModal, setShowApiKeyModal] = React.useState<boolean>(false);
  const [apiKey, setApiKey] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<MessageType[]>([]);
  const [loading, setLoading] = React.useState<boolean>(false);
  const [userTyping, setUserTyping] = React.useState<boolean>(false);
  const [inputDisabled, setInputDisabled] = React.useState<boolean>(false);
  const [userInput, setUserInput] = React.useState<string>("");

  // Scroll helper
  const scrollToBottom = React.useCallback(() => {
    const chatWindow = document.querySelector("#chat-log")?.parentElement;
    chatWindow?.scrollTo(0, chatWindow.scrollHeight);
  }, []);

  // Cookie helpers
  const getCookie = React.useCallback((): [string, string] | undefined => {
    const found = document.cookie
      .split("; ")
      .find((row) => row.startsWith("chatbot_apikey="));
    return found ? (found.split("=") as [string, string]) : undefined;
  }, []);

  const resetCookie = React.useCallback(() => {
    const c = getCookie();
    if (c) document.cookie = `${c[0]}=;expires=Thu, 01 Jan 1970 00:00:00 UTC`;
  }, [getCookie]);

  // Fetch chat log
  const fetchMessages = React.useCallback(async () => {
    if (!apiKey || !selectedModel) return;

    const url = `${baseURL}/`;
    const headers = {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "x-model-id": selectedModel,
    };

    console.log("Calling GET / with:", { url, headers });

    try {
      const res = await fetch(url, {
        method: "GET",
        headers,
      });
      if (!res.ok) throw new Error("Failed to fetch messages");
      const data: MessageType[] = await res.json();
      setMessages(data);
      setTimeout(scrollToBottom, 100);
    } catch (e) {
      console.error("Fetch error:", e);
    }
  }, [apiKey, selectedModel, baseURL, scrollToBottom]);

  // On mount: check API key cookie
  React.useEffect(() => {
    const c = getCookie();
    if (c && c[1]) {
      setApiKey(c[1]);
    } else {
      setShowApiKeyModal(true);
    }
  }, [getCookie]);

  // Enable chat when both pageUrl and selectedModel are set
  const handleStartChat = () => {
    if (!pageUrl.trim() || !selectedModel || !apiKey) return;
    setChatEnabled(true);
    fetchMessages(); // load any existing chat history
  };

  // Send user message
  const handleUserInputSubmit = async (
    e?: React.FormEvent<HTMLFormElement>
  ) => {
    e?.preventDefault();
    if (!userInput.trim() || !chatEnabled || !apiKey) return;

    setInputDisabled(true);
    setUserTyping(false);
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", content: userInput }]);
    setUserInput("");

    const isImage = userInput.toLowerCase().startsWith("/image ");
    const endpoint = isImage ? `${baseURL}/i` : `${baseURL}/`;
    const headers = {
      Accept: "application/json",
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "x-model-id": selectedModel,
    };
    const body = { prompt: userInput };

    console.log(
      "Calling POST to",
      endpoint,
      "with body:",
      body,
      "and headers:",
      headers
    );

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error("Failed to send message");
      await fetchMessages();
    } catch (e) {
      console.error("Send error:", e);
    } finally {
      setLoading(false);
      setInputDisabled(false);
    }
  };

  // Reset chat history
  const onResetClick = async () => {
    if (!apiKey) return;
    setInputDisabled(true);

    const url = `${baseURL}/`;
    const headers = {
      Accept: "application/json",
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "x-model-id": selectedModel,
    };

    console.log("Calling DELETE / with headers:", headers);

    try {
      const res = await fetch(url, {
        method: "DELETE",
        headers,
      });
      if (!res.ok) throw new Error("Failed to reset chat");
      const data: MessageType[] = await res.json();
      setMessages(data);
    } catch (e) {
      console.error("Reset error:", e);
    } finally {
      setInputDisabled(false);
    }
  };

  // Render API key modal if needed
  if (showApiKeyModal) {
    return (
      <ApiKeyModal
        show={showApiKeyModal}
        setShow={setShowApiKeyModal}
        apiKeyError={apiKeyError}
        handleAPIKeyModalClick={() => {
          const inp = document.getElementById(
            "apiKeyInput"
          ) as HTMLInputElement | null;
          if (inp?.value) {
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
    <div className="flex h-screen bg-gray-50">
      {/*** Left Sidebar ***/}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col px-4 py-6 space-y-4">
        {/* Page URL field */}
        <div>
          <label
            htmlFor="pageUrlInput"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Page URL to Scrape
          </label>
          <Input
            id="pageUrlInput"
            type="url"
            placeholder="https://example.com"
            value={pageUrl}
            onChange={(e) => setPageUrl(e.target.value)}
            disabled={chatEnabled || inputDisabled}
          />
        </div>

        {/* Model selector */}
        <div>
          <label
            htmlFor="modelSelect"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Select Model
          </label>
          <Select
            onValueChange={(val) => setSelectedModel(val)}
            disabled={chatEnabled || inputDisabled}
          >
            <SelectTrigger id="modelSelect" className="w-full">
              <SelectValue placeholder="Choose a model…" />
            </SelectTrigger>
            <SelectContent>
              {MODEL_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Start/Reset buttons */}
        <div className="mt-2">
          <Button
            className="w-full"
            onClick={handleStartChat}
            disabled={
              !pageUrl.trim() || !selectedModel || chatEnabled || inputDisabled
            }
          >
            Start Chat
          </Button>

          {chatEnabled && (
            <Button
              variant="outline"
              className="w-full mt-2"
              onClick={onResetClick}
              disabled={inputDisabled}
            >
              Reset Chat
            </Button>
          )}
        </div>
      </div>

      {/*** Right Chat Area ***/}
      <div className="flex-1 flex flex-col">
        {/* Header Bar */}
        <div className="flex items-center justify-between bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-xl font-semibold">Personal Chatbot</h1>
          {chatEnabled && messages.length > 2 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onResetClick}
              disabled={inputDisabled}
            >
              Reset
            </Button>
          )}
        </div>

        {/* Messages Container (flex‐1 so it grows) */}
        <div
          className="flex-1 overflow-y-auto bg-white px-6 py-4"
          id="chat-log"
        >
          <ChatLog
            messages={messages}
            userTyping={userTyping}
            loading={loading}
            scrollToBottom={scrollToBottom}
          />
        </div>

        {/* Input Area (sticky to bottom) */}
        <div className="bg-white border-t border-gray-200 px-6 py-4">
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
  );
};

export default Home;
