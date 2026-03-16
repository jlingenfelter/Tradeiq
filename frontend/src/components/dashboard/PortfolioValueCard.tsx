"use client";

import { formatCurrency, formatPercent } from "@/lib/utils";
import { AnimatedCounter } from "@/components/ui/animated-counter";
import { TrendingUp, TrendingDown } from "lucide-react";

interface Props {
  totalValue: number;
  dailyChange: number;
  dailyChangePct: number;
  currency: string;
}

/* Simple sparkline – 7 synthetic data points trending toward today's change */
function MiniSparkline({ positive }: { positive: boolean }) {
  const color = positive ? "rgba(52,211,153,0.8)" : "rgba(248,113,113,0.8)";
  const fillColor = positive ? "rgba(52,211,153,0.12)" : "rgba(248,113,113,0.12)";

  // Generate a plausible 7-day path
  const points = positive
    ? [38, 34, 40, 36, 42, 39, 48]
    : [42, 44, 38, 41, 36, 39, 32];

  const width = 140;
  const height = 48;
  const maxY = Math.max(...points);
  const minY = Math.min(...points);
  const range = maxY - minY || 1;

  const coords = points.map((p, i) => ({
    x: (i / (points.length - 1)) * width,
    y: height - ((p - minY) / range) * (height - 8) - 4,
  }));

  const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");
  const areaPath = `${linePath} L ${width} ${height} L 0 ${height} Z`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="opacity-60">
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={fillColor} />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#sparkGrad)" />
      <path d={linePath} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function PortfolioValueCard({ totalValue, dailyChange, dailyChangePct, currency }: Props) {
  const isPositive = dailyChange >= 0;

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-800 p-6 md:p-8 shadow-xl animate-fade-in-up">
      {/* Grid pattern overlay */}
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />
      {/* Radial glow */}
      <div className="absolute -top-24 -right-24 w-72 h-72 bg-white/5 rounded-full blur-3xl" />

      <div className="relative flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div className="space-y-1">
          <p className="text-sm font-medium text-indigo-200 tracking-wide uppercase">Portfolio Value</p>
          <div className="text-4xl md:text-5xl font-bold tracking-tight text-white">
            <AnimatedCounter value={totalValue} prefix={currency === "USD" ? "$" : currency + " "} decimals={0} />
          </div>
          <div className="flex items-center gap-3 mt-2">
            <span className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold backdrop-blur-sm ${
              isPositive
                ? "bg-emerald-400/20 text-emerald-200 ring-1 ring-emerald-400/30"
                : "bg-red-400/20 text-red-200 ring-1 ring-red-400/30"
            }`}>
              {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
              {formatPercent(dailyChangePct)}
            </span>
            <span className={`text-sm font-medium ${isPositive ? "text-emerald-300" : "text-red-300"}`}>
              {isPositive ? "+" : "-"}{formatCurrency(Math.abs(dailyChange), currency)} today
            </span>
          </div>
        </div>

        {/* Mini sparkline */}
        <div className="hidden md:block">
          <MiniSparkline positive={isPositive} />
          <p className="text-[10px] text-indigo-300/60 text-right mt-1">7-day trend</p>
        </div>
      </div>
    </div>
  );
}
