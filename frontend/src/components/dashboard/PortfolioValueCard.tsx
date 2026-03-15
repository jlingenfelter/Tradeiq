"use client";

import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency, formatPercent } from "@/lib/utils";

interface Props {
  totalValue: number;
  dailyChange: number;
  dailyChangePct: number;
  currency: string;
}

export function PortfolioValueCard({ totalValue, dailyChange, dailyChangePct, currency }: Props) {
  const isPositive = dailyChange >= 0;
  return (
    <Card>
      <CardContent className="p-6">
        <div className="text-sm font-medium text-neutral-500">Portfolio Value</div>
        <div className="mt-1 text-3xl font-bold">{formatCurrency(totalValue, currency)}</div>
        <div className={`mt-1 text-sm font-medium ${isPositive ? "text-green-600" : "text-red-600"}`}>
          {formatCurrency(Math.abs(dailyChange), currency)} ({formatPercent(dailyChangePct)}) today
        </div>
      </CardContent>
    </Card>
  );
}
