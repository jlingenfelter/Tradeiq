"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Insight {
  icon: string;
  title: string;
  body: string;
  category: "milestone" | "change" | "pattern" | "concentration" | "health";
}

export interface SmartAlert {
  type: string;
  icon: string;
  title: string;
  body: string;
  severity: "success" | "warning" | "info";
  timestamp: string;
}

export function useInsights() {
  return useQuery({
    queryKey: ["insights"],
    queryFn: () => api.get<{ insights: Insight[] }>("/insights"),
    staleTime: 5 * 60_000, // 5 minutes — AI-generated, don't spam
  });
}

export function useSmartAlerts() {
  return useQuery({
    queryKey: ["smart-alerts"],
    queryFn: () => api.get<{ alerts: SmartAlert[] }>("/smart-alerts"),
    staleTime: 60_000,
  });
}
