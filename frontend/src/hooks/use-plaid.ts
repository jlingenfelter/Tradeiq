import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface PlaidAccountInfo {
  id: string;
  name: string;
  official_name: string | null;
  account_type: string;
  current_balance: number | null;
  currency: string;
}

export interface PlaidItem {
  id: string;
  institution_name: string | null;
  status: string;
  created_at: string;
  accounts: PlaidAccountInfo[];
}

export function usePlaidLinkToken() {
  return useMutation({
    mutationFn: () => api.post<{ link_token: string }>("/plaid/link-token"),
  });
}

export function usePlaidExchange() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { public_token: string; institution_id?: string; institution_name?: string }) =>
      api.post("/plaid/exchange", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plaid-items"] });
    },
  });
}

export function usePlaidItems() {
  return useQuery<PlaidItem[]>({
    queryKey: ["plaid-items"],
    queryFn: () => api.get("/plaid/items"),
    staleTime: 60_000,
  });
}

export function usePlaidSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => api.post(`/plaid/sync/${itemId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plaid-items"] });
      qc.invalidateQueries({ queryKey: ["wealth-dashboard"] });
    },
  });
}

export function usePlaidDelete() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => api.delete(`/plaid/items/${itemId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plaid-items"] });
    },
  });
}
