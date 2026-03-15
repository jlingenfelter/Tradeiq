"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatMessageBubble } from "./ChatMessage";
import { Send, RotateCcw } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  messages: Message[];
  onSend: (message: string) => void;
  onClear: () => void;
  isLoading: boolean;
}

const SUGGESTED_QUESTIONS = [
  "What is my current net worth?",
  "How liquid am I?",
  "What is my biggest concentration?",
  "How leveraged am I?",
  "What should I review first?",
  "What would happen if my stocks fell 20%?",
  "How much of my wealth is in property?",
];

export function ChatWindow({ messages, onSend, onClear, isLoading }: Props) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput("");
  }

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="space-y-4 pt-8">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-neutral-700">Ask about your wealth</h3>
              <p className="text-sm text-neutral-500 mt-1">
                Get AI-powered insights based on your actual financial data
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => onSend(q)}
                  className="text-sm bg-neutral-100 hover:bg-neutral-200 rounded-full px-4 py-2 text-neutral-700 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessageBubble key={i} role={msg.role} content={msg.content} />
        ))}

        {isLoading && (
          <div className="flex gap-2 items-center px-4">
            <div className="h-2 w-2 rounded-full bg-neutral-400 animate-pulse" />
            <div className="h-2 w-2 rounded-full bg-neutral-400 animate-pulse delay-100" />
            <div className="h-2 w-2 rounded-full bg-neutral-400 animate-pulse delay-200" />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-neutral-200 pt-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your wealth..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={!input.trim() || isLoading} size="icon">
            <Send className="h-4 w-4" />
          </Button>
          {messages.length > 0 && (
            <Button type="button" variant="outline" size="icon" onClick={onClear}>
              <RotateCcw className="h-4 w-4" />
            </Button>
          )}
        </form>
      </div>
    </div>
  );
}
