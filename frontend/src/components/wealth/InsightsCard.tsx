"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useInsights } from "@/hooks/use-insights";
import { Sparkles } from "lucide-react";

const CATEGORY_COLORS: Record<string, string> = {
  milestone: "bg-amber-50 border-amber-200",
  change: "bg-blue-50 border-blue-200",
  pattern: "bg-indigo-50 border-indigo-200",
  concentration: "bg-orange-50 border-orange-200",
  health: "bg-emerald-50 border-emerald-200",
};

export function InsightsCard() {
  const { data, isLoading } = useInsights();

  const insights = data?.insights ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-500" />
          <CardTitle className="text-base">AI Insights</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 rounded-md bg-neutral-100 animate-pulse" />
            ))}
          </div>
        ) : insights.length === 0 ? (
          <p className="text-sm text-neutral-400 text-center py-6">
            Add more data to unlock AI-powered insights.
          </p>
        ) : (
          <div className="space-y-2.5">
            {insights.map((insight, i) => (
              <div
                key={i}
                className={`rounded-lg border px-4 py-3 ${CATEGORY_COLORS[insight.category] || "bg-neutral-50 border-neutral-200"}`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg leading-none mt-0.5">{insight.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{insight.title}</p>
                    <p className="text-xs text-neutral-600 mt-0.5">{insight.body}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
