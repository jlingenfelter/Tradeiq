import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface TrueLayerAccountInfo {
  id: string;
  name: string;
  account_type: string;
  current_balance: number | null;
  currency: string;
}

export interface TrueLayerConnection {
  id: string;
  provider_name: string | null;
  status: string;
  created_at: string;
  accounts: TrueLayerAccountInfo[];
}

export function useTrueLayerAuthUrl() {
  return useMutation({
    mutationFn: () => api.post<{ auth_url: string }>("/truelayer/auth-url"),
  });
}

export function useTrueLayerExchange() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { code: string; redirect_uri: string }) =>
      api.post("/truelayer/exchange", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["truelayer-connections"] });
    },
  });
}

export function useTrueLayerConnections() {
  return useQuery<TrueLayerConnection[]>({
    queryKey: ["truelayer-connections"],
    queryFn: () => api.get("/truelayer/connections"),
    staleTime: 60_000,
  });
}

export function useTrueLayerSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) => api.post(`/truelayer/sync/${connectionId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["truelayer-connections"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

export function useTrueLayerDelete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (connectionId: string) => api.delete(`/truelayer/connections/${connectionId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["truelayer-connections"] });
    },
  });
}
