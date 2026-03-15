"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { HealthScoreBreakdown } from "@/types";

interface Props {
  score: number;
  breakdown: HealthScoreBreakdown;
}

function scoreColor(score: number): string {
  if (score >= 75) return "text-emerald-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-600";
}

function scoreGradient(score: number): string {
  if (score >= 75) return "from-emerald-500 to-emerald-400";
  if (score >= 50) return "from-amber-500 to-amber-400";
  return "from-red-500 to-red-400";
}

function scoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  return "Needs Attention";
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
        <div className="text-sm font-medium text-slate-500">Health Score</div>
        <div className="flex items-end gap-2 mt-1">
          <span className={`text-4xl font-bold ${scoreColor(score)}`}>{score}</span>
          <span className="text-sm text-slate-400 pb-1">/ 100</span>
        </div>
        <div className={`text-xs font-medium mt-0.5 ${scoreColor(score)}`}>{scoreLabel(score)}</div>
        <div className="mt-4 space-y-2.5">
          {factors.map((f) => (
            <div key={f.label} className="flex items-center gap-2">
              <div className="w-28 text-xs text-slate-500 truncate">{f.label}</div>
              <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${scoreGradient(f.value)}`}
                  style={{ width: `${f.value}%` }}
                />
              </div>
              <div className="w-8 text-xs text-right font-medium text-slate-600">{f.value}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
