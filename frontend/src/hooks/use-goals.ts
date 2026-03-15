"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { WealthGoal, WeeklyRecap } from "@/types";

export function useGoals() {
  return useQuery({
    queryKey: ["goals"],
    queryFn: () => api.get<WealthGoal[]>("/goals"),
    staleTime: 30_000,
  });
}

export function useCreateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      name: string;
      target_amount: number;
      target_date?: string;
      goal_type?: string;
      emoji?: string;
      notes?: string;
    }) => api.post("/goals", data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
    },
  });
}

export function useUpdateGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: { id: string } & Record<string, unknown>) =>
      api.patch(`/goals/${id}`, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
    },
  });
}

export function useDeleteGoal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/goals/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["goals"] });
    },
  });
}

export function useWeeklyRecap() {
  return useQuery({
    queryKey: ["weekly-recap"],
    queryFn: () => api.get<WeeklyRecap>("/recap/weekly"),
    staleTime: 60_000 * 5,
  });
}
