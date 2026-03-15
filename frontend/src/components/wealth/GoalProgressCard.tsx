"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useGoals } from "@/hooks/use-goals";
import { formatCurrency } from "@/lib/utils";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export function GoalProgressCard() {
  const { data: goals, isLoading } = useGoals();

  if (isLoading || !goals || goals.length === 0) return null;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Goals</CardTitle>
          <Link
            href="/goals"
            className="text-xs text-neutral-500 hover:text-neutral-900 flex items-center gap-1"
          >
            Manage <ArrowRight className="h-3 w-3" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {goals.slice(0, 3).map((goal) => {
            const pct = Math.min(100, goal.progress_pct);
            const color =
              pct >= 100 ? "bg-green-500" : pct >= 50 ? "bg-indigo-500" : pct >= 25 ? "bg-amber-500" : "bg-slate-300";
            return (
              <div key={goal.id}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">
                    {goal.emoji} {goal.name}
                  </span>
                  <span className="text-xs text-neutral-500">
                    {Math.round(pct)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-neutral-100 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${color} transition-all duration-700 ease-out`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <p className="text-xs text-neutral-400 mt-0.5">
                  {formatCurrency(goal.current_value, goal.currency)} / {formatCurrency(goal.target_amount, goal.currency)}
                </p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
