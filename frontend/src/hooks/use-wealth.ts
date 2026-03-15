"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type {
  WealthDashboardResponse,
  Asset,
  Liability,
  WealthContainer,
  NetWorthHistoryItem,
} from "@/types";

// ── Wealth Dashboard ──

export function useWealthDashboard() {
  return useQuery({
    queryKey: ["wealth-dashboard"],
    queryFn: () => api.get<WealthDashboardResponse>("/dashboard/overview"),
    staleTime: 30_000,
  });
}

export function useWealthAllocation() {
  return useQuery({
    queryKey: ["wealth-allocation"],
    queryFn: () => api.get<Record<string, unknown>>("/dashboard/allocation"),
    staleTime: 30_000,
  });
}

export function useNetWorthHistory() {
  return useQuery({
    queryKey: ["net-worth-history"],
    queryFn: () => api.get<{ history: NetWorthHistoryItem[] }>("/dashboard/net-worth-history"),
    staleTime: 60_000,
  });
}

// ── Assets ──

export function useAssets(assetClass?: string) {
  const params = assetClass ? `?asset_class=${assetClass}` : "";
  return useQuery({
    queryKey: ["assets", assetClass],
    queryFn: () => api.get<Asset[]>(`/assets${params}`),
    staleTime: 30_000,
  });
}

export function useCreateAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Asset>) => api.post<Asset>("/assets", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

export function useUpdateAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Asset> & { id: string }) =>
      api.patch<Asset>(`/assets/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

export function useDeleteAsset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/assets/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["assets"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

// ── Liabilities ──

export function useLiabilities() {
  return useQuery({
    queryKey: ["liabilities"],
    queryFn: () => api.get<Liability[]>("/liabilities"),
    staleTime: 30_000,
  });
}

export function useCreateLiability() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Liability>) => api.post<Liability>("/liabilities", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["liabilities"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

export function useUpdateLiability() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: Partial<Liability> & { id: string }) =>
      api.patch<Liability>(`/liabilities/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["liabilities"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

export function useDeleteLiability() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/liabilities/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["liabilities"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

// ── Containers ──

export function useContainers() {
  return useQuery({
    queryKey: ["containers"],
    queryFn: () => api.get<WealthContainer[]>("/containers"),
    staleTime: 60_000,
  });
}

export function useCreateContainer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<WealthContainer>) => api.post<WealthContainer>("/containers", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["containers"] });
    },
  });
}
