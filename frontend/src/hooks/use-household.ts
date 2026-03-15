import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface HouseholdMember {
  id: string;
  email: string;
  name: string | null;
  status: "pending" | "accepted";
  role: string;
  joined_at: string | null;
}

export interface Household {
  id: string;
  name: string;
  owner_id: string;
  members: HouseholdMember[];
  created_at: string;
}

export interface CombinedWealth {
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  currency: string;
  members: {
    name: string;
    net_worth: number;
  }[];
}

export interface HouseholdGoal {
  id: string;
  name: string;
  target_amount: number;
  current_value: number;
  progress_pct: number;
  currency: string;
  created_at: string;
}

export function useHousehold() {
  return useQuery<Household | null>({
    queryKey: ["household"],
    queryFn: () => api.get("/household"),
    staleTime: 60_000,
  });
}

export function useCreateHousehold() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string }) => api.post<Household>("/household", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["household"] });
    },
  });
}

export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { email: string }) => api.post("/household/invite", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["household"] });
    },
  });
}

export function useCombinedWealth() {
  return useQuery<CombinedWealth>({
    queryKey: ["household-combined"],
    queryFn: () => api.get("/household/combined"),
    staleTime: 60_000,
  });
}

export function useHouseholdGoals() {
  return useQuery<HouseholdGoal[]>({
    queryKey: ["household-goals"],
    queryFn: () => api.get("/household/goals"),
    staleTime: 60_000,
  });
}

export function useCreateHouseholdGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; target_amount: number }) =>
      api.post<HouseholdGoal>("/household/goals", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["household-goals"] });
    },
  });
}
