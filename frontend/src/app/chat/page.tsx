"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ChatWindow } from "@/components/chat/ChatWindow";
import { useWealthChat } from "@/hooks/use-chat";

export default function ChatPage() {
  const { messages, sendMessage, isLoading, clearChat } = useWealthChat();

  return (
    <AppShell>
      <div className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold">Ask AI</h2>
          <p className="text-sm text-neutral-500">
            Ask questions about your wealth — answers are based on your actual data
          </p>
        </div>

        <ChatWindow
          messages={messages}
          onSend={sendMessage}
          onClear={clearChat}
          isLoading={isLoading}
        />
      </div>
    </AppShell>
  );
}
