"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DashboardResponse, Warning } from "@/types";

interface AnalyticsLatest {
  total_value: number;
  health_score: number;
  holdings: Array<{
    symbol: string;
    name: string;
    quantity: number;
    price: number;
    market_value: number;
    weight: number;
    unrealized_pnl: number | null;
    sector: string | null;
    country: string | null;
  }>;
  sector_exposure: Record<string, number>;
  country_exposure: Record<string, number>;
  stress_tests: unknown[];
  benchmark_comparison: unknown[];
  position_count: number;
  n_sectors: number;
  n_countries: number;
  hhi: number;
}

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
  return useQuery<AnalyticsLatest>({
    queryKey: ["analytics", portfolioId],
    queryFn: () => api.get(`/portfolios/${portfolioId}/analytics/latest`),
    enabled: !!portfolioId,
    staleTime: 60_000,
  });
}

export interface ConnectionInfo {
  id: string;
  portfolio_id: string;
  name: string;
  source_type: string;
  environment: string | null;
  auto_sync: boolean;
  last_synced_at: string | null;
  sync_error: string | null;
  position_count: number;
}

export function useConnections(portfolioId: string) {
  return useQuery<ConnectionInfo[]>({
    queryKey: ["connections", portfolioId],
    queryFn: () => api.get(`/portfolios/${portfolioId}/connections`),
    enabled: !!portfolioId,
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
