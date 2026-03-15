import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface ScenarioInput {
  type: "mortgage_payoff" | "savings_projection" | "asset_change" | "debt_snowball";
  params: Record<string, unknown>;
}

export interface ScenarioDataPoint {
  month: number;
  label: string;
  value: number;
  principal?: number;
  interest?: number;
}

export interface ScenarioResult {
  type: string;
  data: ScenarioDataPoint[];
  summary: Record<string, number | string>;
}

export function useRunScenario() {
  return useMutation({
    mutationFn: (input: ScenarioInput) =>
      api.post<ScenarioResult>("/scenarios/run", input),
  });
}
