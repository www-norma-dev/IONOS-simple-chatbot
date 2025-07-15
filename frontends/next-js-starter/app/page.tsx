// src/pages/Home.tsx
"use client";
import * as React from "react";
import ChatLog from "@/components/ChatLog";
import TextInput from "@/components/TextInput";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";

interface ModelOption {
  label: string; 
  value: string; // 
}

const MODEL_OPTIONS = [
  {
    label: "meta-llama/Meta-Llama-3.1-8B-Instruct",
    value: "meta-llama/Meta-Llama-3.1-8B-Instruct",
  },
  {
    label: "meta-llama/Llama-3.3-70B-Instruct",
    value: "meta-llama/Llama-3.3-70B-Instruct",
  },
  {
    label: "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8",
    value: "meta-llama/Meta-Llama-3.1-405B-Instruct-FP8",
  },
];

export default function Home() {
  const baseURL =
    process.env.NEXT_PUBLIC_APP_BASE_URL ?? "http://localhost:8000";

  // Page + model selection
  const [pageUrl, setPageUrl] = React.useState("");
  const [selectedModel, setSelectedModel] = React.useState<string>("");

  // Chat UI state
  const [chatEnabled, setChatEnabled] = React.useState(false);
  const [messages, setMessages] = React.useState<any>([]);
  const [loading, setLoading] = React.useState(false);
  const [userTyping, setUserTyping] = React.useState(false);
  const [inputDisabled, setInputDisabled] = React.useState(false);
  const [userInput, setUserInput] = React.useState("");

  const scrollToBottom = React.useCallback(() => {
    const chatWindow = document.querySelector("#chat-log")?.parentElement;
    chatWindow?.scrollTo(0, chatWindow.scrollHeight);
  }, []);

  // Fetch messages from GET /
  const fetchMessages = React.useCallback(async () => {
    if (!selectedModel) return;
    const res = await fetch(`${baseURL}/`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "x-model-id": "mistralai/Mixtral-8x7B-Instruct-v0.1", // <-- send the LABEL here
      },
    });
    if (res.ok) {
      const raw = (await res.json()) as Array<{
        content: string;
        type: string;
      }>;
      const ui = raw
        .filter((m) => m.type === "human" || m.type === "ai")
        .map((m) => ({
          role: m.type === "human" ? "user" : "assistant",
          content: m.content,
        }));
      setMessages(ui);
      setTimeout(scrollToBottom, 100);
    }
  }, [baseURL, selectedModel, scrollToBottom]);

  // Kick off RAG init + enable chat
  const handleStartChat = async () => {
    if (!pageUrl.trim() || !selectedModel) return;
    setInputDisabled(true);
    try {
      const initRes = await fetch(`${baseURL}/init`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ page_url: pageUrl }),
      });
      if (!initRes.ok) throw new Error("Failed to initialize RAG index");
      setChatEnabled(true);
      await fetchMessages();
    } catch (err) {
      console.error(err);
    } finally {
      setInputDisabled(false);
    }
  };

  // Send user message to POST /
  const handleUserInputSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!userInput.trim() || !chatEnabled) return;

    setUserTyping(false);
    setInputDisabled(true);
    setLoading(true);
    setMessages((prev: any) => [...prev, { role: "user", content: userInput }]);
    setUserInput("");

    try {
      const res = await fetch(`${baseURL}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-model-id": selectedModel,
        },
        body: JSON.stringify({ prompt: userInput }),
      });
      if (!res.ok) throw new Error("Failed to send message");
      await fetchMessages();
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setInputDisabled(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/*** Sidebar ***/}
      <div className="w-64 bg-white border-r border-gray-200 p-6 space-y-4">
        <div>
          <label
            htmlFor="pageUrlInput"
            className="block text-sm font-medium mb-1"
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

        <div>
          <label
            htmlFor="modelSelect"
            className="block text-sm font-medium mb-1"
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

        <Button
          className="w-full"
          onClick={handleStartChat}
          disabled={!pageUrl.trim() || !selectedModel || inputDisabled}
        >
          Start Chat
        </Button>
      </div>

      {/*** Chat Area ***/}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between border-b px-6 py-4 bg-white">
          <h1 className="text-xl font-semibold">Personal Chatbot</h1>
        </div>

        <div id="chat-log" className="flex-1 overflow-y-auto p-6 bg-white">
          <ChatLog
            messages={messages}
            userTyping={userTyping}
            loading={loading}
            scrollToBottom={scrollToBottom}
          />
        </div>

        <div className="border-t px-6 py-4 bg-white">
          <TextInput
            userTyping={userTyping}
            setUserTyping={setUserTyping}
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
}
