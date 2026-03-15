"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useChat } from "@/hooks/use-chat";

export default function ChatPage() {
  const { data: portfolios } = usePortfolios();
  const [portfolioId, setPortfolioId] = useState("");

  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !portfolioId) {
      setPortfolioId(portfolios[0].id);
    }
  }, [portfolios, portfolioId]);

  const { messages, sendMessage, isLoading, clearChat } = useChat(portfolioId);

  return (
    <AppShell>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Ask AI</h2>
            <p className="text-sm text-neutral-500">
              Ask questions about your portfolio — answers are based on your actual data
            </p>
          </div>
          {portfolios && portfolios.length > 1 && (
            <select
              className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
              value={portfolioId}
              onChange={(e) => {
                setPortfolioId(e.target.value);
                clearChat();
              }}
            >
              {portfolios.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          )}
        </div>

        {portfolioId ? (
          <ChatWindow
            messages={messages}
            onSend={sendMessage}
            onClear={clearChat}
            isLoading={isLoading}
          />
        ) : (
          <div className="text-neutral-500">Loading...</div>
        )}
      </div>
    </AppShell>
  );
}
