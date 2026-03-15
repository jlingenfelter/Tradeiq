"use client";

import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

interface Props {
  totalValue: number;
  dailyChange: number;
  dailyChangePct: number;
  currency: string;
}

export function PortfolioValueCard({ totalValue, dailyChange, dailyChangePct, currency }: Props) {
  const isPositive = dailyChange >= 0;
  return (
    <Card className="overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 pointer-events-none" />
      <CardContent className="p-6 relative">
        <div className="flex items-center justify-between">
          <div className="text-sm font-medium text-slate-500">Portfolio Value</div>
          <div className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${
            isPositive ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"
          }`}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {formatPercent(dailyChangePct)}
          </div>
        </div>
        <div className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
          {formatCurrency(totalValue, currency)}
        </div>
        <div className={`mt-1 text-sm font-medium ${isPositive ? "text-emerald-600" : "text-red-600"}`}>
          {isPositive ? "+" : "-"}{formatCurrency(Math.abs(dailyChange), currency)} today
        </div>
      </CardContent>
    </Card>
  );
}
