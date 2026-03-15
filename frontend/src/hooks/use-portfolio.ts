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

export function useUpdatePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string; name?: string; base_currency?: string }) =>
      api.patch<Portfolio>(`/portfolios/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolios"] });
    },
  });
}

export function useDeletePortfolio() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/portfolios/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["portfolios"] }),
  });
}

export function useDeletePosition() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ portfolioId, positionId }: { portfolioId: string; positionId: string }) =>
      api.delete(`/portfolios/${portfolioId}/positions/${positionId}`),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ["positions", vars.portfolioId] });
    },
  });
}
