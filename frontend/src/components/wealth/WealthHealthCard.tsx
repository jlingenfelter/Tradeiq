"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { WealthHealthBreakdown } from "@/types";

interface Props {
  score: number;
  breakdown: WealthHealthBreakdown;
}

const COMPONENT_LABELS: Record<string, { label: string; weight: string }> = {
  liquidity: { label: "Liquidity", weight: "25%" },
  concentration: { label: "Concentration", weight: "20%" },
  leverage: { label: "Leverage", weight: "20%" },
  diversification: { label: "Diversification", weight: "20%" },
  public_market_risk: { label: "Market Risk", weight: "10%" },
  data_freshness: { label: "Data Freshness", weight: "5%" },
};

function getScoreColor(score: number): string {
  if (score >= 75) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  if (score >= 25) return "text-orange-600";
  return "text-red-600";
}

function getBarColor(score: number): string {
  if (score >= 75) return "bg-green-500";
  if (score >= 50) return "bg-yellow-500";
  if (score >= 25) return "bg-orange-500";
  return "bg-red-500";
}

export function WealthHealthCard({ score, breakdown }: Props) {
  const components = Object.entries(COMPONENT_LABELS).map(([key, meta]) => ({
    key,
    label: meta.label,
    weight: meta.weight,
    score: (breakdown as unknown as Record<string, number>)[key] || 0,
  }));

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Wealth Health Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-6">
          <div className={`text-4xl font-bold ${getScoreColor(score)}`}>
            {score}
          </div>
          <div className="text-sm text-neutral-500">out of 100</div>
        </div>
        <div className="space-y-3">
          {components.map((comp) => (
            <div key={comp.key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-neutral-600">{comp.label}</span>
                <span className="text-xs text-neutral-400">{comp.score}/100 ({comp.weight})</span>
              </div>
              <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${getBarColor(comp.score)}`}
                  style={{ width: `${comp.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
