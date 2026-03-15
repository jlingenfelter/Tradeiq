"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useWeeklyRecap } from "@/hooks/use-goals";
import { formatCurrency } from "@/lib/utils";
import { TrendingUp, TrendingDown, Clock, Flame, ArrowUpRight, ArrowDownRight } from "lucide-react";

export function WeeklyRecapCard() {
  const { data, isLoading } = useWeeklyRecap();

  if (isLoading || !data || !data.weekly_change) return null;

  const isUp = data.weekly_change >= 0;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Weekly Recap</CardTitle>
          {data.growth_streak > 1 && (
            <Badge variant="secondary" className="text-xs gap-1">
              <Flame className="h-3 w-3 text-orange-500" />
              {data.growth_streak} week streak
            </Badge>
          )}
        </div>
        <p className="text-sm text-neutral-500">{data.headline}</p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main change */}
        <div className={`flex items-center gap-3 rounded-lg p-3 ${isUp ? "bg-green-50" : "bg-red-50"}`}>
          <div className={`rounded-full p-2 ${isUp ? "bg-green-100" : "bg-red-100"}`}>
            {isUp ? (
              <TrendingUp className="h-5 w-5 text-green-600" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-600" />
            )}
          </div>
          <div>
            <p className={`text-lg font-bold ${isUp ? "text-green-700" : "text-red-700"}`}>
              {isUp ? "+" : ""}{formatCurrency(data.weekly_change, data.currency)}
            </p>
            <p className="text-xs text-neutral-500">
              {isUp ? "+" : ""}{data.weekly_change_pct.toFixed(2)}% this week
            </p>
          </div>
        </div>

        {/* Fun stats */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border p-3">
            <div className="flex items-center gap-1.5 text-neutral-500 mb-1">
              <Clock className="h-3.5 w-3.5" />
              <span className="text-xs">Per hour</span>
            </div>
            <p className={`text-sm font-semibold ${data.per_hour >= 0 ? "text-green-600" : "text-red-600"}`}>
              {data.per_hour >= 0 ? "+" : ""}{formatCurrency(data.per_hour, data.currency)}
            </p>
            <p className="text-xs text-neutral-400">while you slept</p>
          </div>
          <div className="rounded-lg border p-3">
            <div className="flex items-center gap-1.5 text-neutral-500 mb-1">
              <TrendingUp className="h-3.5 w-3.5" />
              <span className="text-xs">This month</span>
            </div>
            <p className={`text-sm font-semibold ${data.monthly_change >= 0 ? "text-green-600" : "text-red-600"}`}>
              {data.monthly_change >= 0 ? "+" : ""}{formatCurrency(data.monthly_change, data.currency)}
            </p>
            <p className="text-xs text-neutral-400">
              {data.monthly_change_pct >= 0 ? "+" : ""}{data.monthly_change_pct.toFixed(1)}%
            </p>
          </div>
        </div>

        {/* Top movers */}
        {data.top_movers.length > 0 && (
          <div>
            <p className="text-xs font-medium text-neutral-500 mb-2">Biggest movers</p>
            <div className="space-y-1.5">
              {data.top_movers.map((m) => (
                <div key={m.category} className="flex items-center justify-between text-sm">
                  <span className="text-neutral-700">{m.category}</span>
                  <div className="flex items-center gap-1">
                    {m.change >= 0 ? (
                      <ArrowUpRight className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <ArrowDownRight className="h-3.5 w-3.5 text-red-500" />
                    )}
                    <span className={m.change >= 0 ? "text-green-600" : "text-red-600"}>
                      {m.change >= 0 ? "+" : ""}{formatCurrency(m.change, data.currency)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
