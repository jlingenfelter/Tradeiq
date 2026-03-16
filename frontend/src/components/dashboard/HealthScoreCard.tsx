"use client";

import { Card, CardContent } from "@/components/ui/card";
import type { HealthScoreBreakdown } from "@/types";

interface Props {
  score: number;
  breakdown: HealthScoreBreakdown;
}

function scoreColor(score: number): string {
  if (score >= 75) return "#10b981"; // emerald
  if (score >= 50) return "#f59e0b"; // amber
  return "#ef4444"; // red
}

function scoreColorClass(score: number): string {
  if (score >= 75) return "text-emerald-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-600";
}

function scoreGradient(score: number): string {
  if (score >= 75) return "from-emerald-500 to-emerald-400";
  if (score >= 50) return "from-amber-500 to-amber-400";
  return "from-red-500 to-red-400";
}

function scoreBgClass(score: number): string {
  if (score >= 75) return "bg-emerald-50";
  if (score >= 50) return "bg-amber-50";
  return "bg-red-50";
}

function scoreLabel(score: number): string {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Fair";
  return "Needs Attention";
}

/* Circular progress ring */
function ScoreRing({ score }: { score: number }) {
  const size = 140;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = scoreColor(score);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Background ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-slate-100 dark:text-slate-800"
          strokeWidth={strokeWidth}
        />
        {/* Progress ring */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="health-ring-animate"
          style={{
            "--ring-offset": circumference,
            "--ring-target": offset,
          } as React.CSSProperties}
        />
      </svg>
      {/* Center score */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-bold ${scoreColorClass(score)}`}>{score}</span>
        <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">/ 100</span>
      </div>
    </div>
  );
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
    <Card className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
      <CardContent className="p-6">
        <div className="text-sm font-medium text-slate-500 mb-4">Health Score</div>

        <div className="flex items-start gap-6">
          {/* Ring */}
          <ScoreRing score={score} />

          {/* Label + Factors */}
          <div className="flex-1 min-w-0">
            <span className={`inline-block text-xs font-semibold px-2.5 py-1 rounded-full ${scoreBgClass(score)} ${scoreColorClass(score)}`}>
              {scoreLabel(score)}
            </span>

            <div className="mt-3 space-y-2.5">
              {factors.map((f) => (
                <div key={f.label} className="flex items-center gap-2">
                  <div className="w-24 text-[11px] text-slate-500 truncate">{f.label}</div>
                  <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full bg-gradient-to-r ${scoreGradient(f.value)} transition-all duration-1000 ease-out`}
                      style={{ width: `${f.value}%` }}
                    />
                  </div>
                  <div className="w-7 text-[11px] text-right font-semibold text-slate-600">{f.value}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
