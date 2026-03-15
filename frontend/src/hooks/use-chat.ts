"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  answer: string;
  session_id: string;
}

export function useChat(portfolioId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: async (question: string) => {
      setMessages((prev) => [...prev, { role: "user", content: question }]);
      const res = await api.post<ChatResponse>(`/portfolios/${portfolioId}/chat`, {
        question,
        session_id: sessionId,
      });
      return res;
    },
    onSuccess: (data) => {
      setSessionId(data.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, I was unable to process your question. Please try again." },
      ]);
    },
  });

  function clearChat() {
    setMessages([]);
    setSessionId(null);
  }

  return {
    messages,
    sendMessage: mutation.mutate,
    isLoading: mutation.isPending,
    clearChat,
    sessionId,
  };
}
