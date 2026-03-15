"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Portfolio, Position } from "@/types";

export function usePortfolios() {
  return useQuery<Portfolio[]>({
    queryKey: ["portfolios"],
    queryFn: () => api.get("/portfolios"),
  });
}

export function usePortfolio(id: string) {
  return useQuery<Portfolio>({
    queryKey: ["portfolio", id],
    queryFn: () => api.get(`/portfolios/${id}`),
    enabled: !!id,
  });
}

export function usePositions(portfolioId: string) {
  return useQuery<Position[]>({
    queryKey: ["positions", portfolioId],
    queryFn: () => api.get(`/portfolios/${portfolioId}/positions`),
    enabled: !!portfolioId,
  });
}

export function useCreatePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; base_currency?: string }) =>
      api.post<Portfolio>("/portfolios", data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolios"] }),
  });
}
