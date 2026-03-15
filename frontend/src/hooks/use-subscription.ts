import { useQuery, useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface SubscriptionInfo {
  tier: "free" | "pro" | "family";
  status: "active" | "canceled" | "past_due" | "trialing";
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export function useSubscription() {
  return useQuery<SubscriptionInfo>({
    queryKey: ["subscription"],
    queryFn: () => api.get("/billing/subscription"),
    staleTime: 60_000,
  });
}

export function useCreateCheckout() {
  return useMutation({
    mutationFn: (tier: "pro" | "family") =>
      api.post<{ url: string }>("/billing/checkout", { tier }),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });
}

export function useCreatePortal() {
  return useMutation({
    mutationFn: () => api.post<{ url: string }>("/billing/portal"),
    onSuccess: (data) => {
      window.location.href = data.url;
    },
  });
}
