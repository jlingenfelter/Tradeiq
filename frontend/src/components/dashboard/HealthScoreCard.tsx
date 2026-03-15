"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { HealthScoreBreakdown } from "@/types";

interface Props {
  score: number;
  breakdown: HealthScoreBreakdown;
}

function scoreColor(score: number): string {
  if (score >= 75) return "text-green-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-600";
}

function scoreBg(score: number): string {
  if (score >= 75) return "bg-green-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-red-500";
}

export function HealthScoreCard({ score, breakdown }: Props) {
  const factors = [
    { label: "Diversification", value: breakdown.diversification },
    { label: "Stock Concentration", value: breakdown.single_stock_concentration },
    { label: "Sector Concentration", value: breakdown.sector_concentration },
    { label: "Resilience", value: breakdown.resilience },
    { label: "Benchmark Balance", value: breakdown.benchmark_balance },
    { label: "Event Risk", value: breakdown.event_risk },
  ];

  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-sm font-medium text-neutral-500">Health Score</div>
        <div className={`mt-1 text-4xl font-bold ${scoreColor(score)}`}>{score}</div>
        <div className="mt-3 space-y-2">
          {factors.map((f) => (
            <div key={f.label} className="flex items-center gap-2">
              <div className="w-28 text-xs text-neutral-500 truncate">{f.label}</div>
              <div className="flex-1 h-2 bg-neutral-100 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${scoreBg(f.value)}`} style={{ width: `${f.value}%` }} />
              </div>
              <div className="w-8 text-xs text-right text-neutral-600">{f.value}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
