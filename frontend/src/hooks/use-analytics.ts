"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DashboardResponse, Warning } from "@/types";

export function useDashboard(portfolioId: string) {
  return useQuery<DashboardResponse>({
    queryKey: ["dashboard", portfolioId],
    queryFn: () => api.get(`/portfolios/${portfolioId}/dashboard`),
    enabled: !!portfolioId,
    staleTime: 60_000,
  });
}

export function useWarnings(portfolioId: string, severity?: string) {
  const params = severity ? `?severity=${severity}` : "";
  return useQuery<Warning[]>({
    queryKey: ["warnings", portfolioId, severity],
    queryFn: () => api.get(`/portfolios/${portfolioId}/warnings${params}`),
    enabled: !!portfolioId,
  });
}

export function useAnalyticsLatest(portfolioId: string) {
  return useQuery({
    queryKey: ["analytics", portfolioId],
    queryFn: () => api.get(`/portfolios/${portfolioId}/analytics/latest`),
    enabled: !!portfolioId,
    staleTime: 60_000,
  });
}

export function useRecomputeAnalytics(portfolioId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(`/portfolios/${portfolioId}/analytics/recompute`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", portfolioId] });
      queryClient.invalidateQueries({ queryKey: ["analytics", portfolioId] });
      queryClient.invalidateQueries({ queryKey: ["warnings", portfolioId] });
    },
  });
}
