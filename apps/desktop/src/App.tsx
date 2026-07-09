import { useEffect, useState } from "react";
import "./App.css";

import type { Message } from "./types";
import { sendMessage } from "./api";

const STORAGE_KEY = "fumi:chat";

export default function App() {
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);

    if (saved) {
      return JSON.parse(saved);
    }

    return [
      {
        text: "hey.",
        sender: "assistant",
      },
    ];
  });

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userText = input;

    setMessages((prev) => [
      ...prev,
      {
        text: userText,
        sender: "user",
      },
    ]);

    setInput("");
    setIsTyping(true);

    try {
      const reply = await sendMessage(userText);

      setMessages((prev) => [
        ...prev,
        {
          text: reply,
          sender: "assistant",
        },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          text: "backend unavailable.",
          sender: "assistant",
        },
      ]);
    } finally {
      // Runs whether the request succeeds or fails
      setIsTyping(false);
    }
  };

  return (
    <div className="app">
      <div className="messages">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`bubble-row ${message.sender}`}
          >
            <div className={`bubble ${message.sender}`}>
              {message.text}
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="bubble-row assistant">
            <div className="typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
      </div>

      <div className="input-area">
        <input
          value={input}
          disabled={isTyping}
          placeholder="Message Fumi..."
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              handleSend();
            }
          }}
        />

        <button
          onClick={handleSend}
          disabled={isTyping}
        >
          ↑
        </button>
      </div>
    </div>
  );
}