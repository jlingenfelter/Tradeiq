"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { useInsights } from "@/hooks/use-insights";
import { Lightbulb, Sparkles } from "lucide-react";

const CATEGORY_COLORS: Record<string, string> = {
  milestone: "bg-amber-50 border-amber-200",
  change: "bg-blue-50 border-blue-200",
  pattern: "bg-indigo-50 border-indigo-200",
  concentration: "bg-orange-50 border-orange-200",
  health: "bg-emerald-50 border-emerald-200",
};

const CATEGORY_LABELS: Record<string, string> = {
  milestone: "Milestone",
  change: "Change",
  pattern: "Pattern",
  concentration: "Concentration",
  health: "Health",
};

export default function InsightsPage() {
  const { data, isLoading } = useInsights();

  const insights = data?.insights ?? [];

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-500" />
            <h2 className="text-2xl font-bold">AI Insights</h2>
          </div>
          <p className="text-sm text-neutral-500 mt-1">
            AI-generated observations about your wealth data. These are factual highlights, not financial advice.
          </p>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-20 rounded-lg bg-neutral-100 animate-pulse" />
            ))}
          </div>
        ) : insights.length === 0 ? (
          <EmptyState
            icon={Lightbulb}
            title="Insights coming soon"
            description="Once you have portfolio data, we'll generate personalized insights"
          />
        ) : (
          <div className="space-y-3">
            {insights.map((insight, i) => (
              <Card
                key={i}
                className={`border ${CATEGORY_COLORS[insight.category] || "border-neutral-200"}`}
              >
                <CardContent className="p-5">
                  <div className="flex items-start gap-4">
                    <span className="text-2xl">{insight.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold">{insight.title}</p>
                        <span className="text-[10px] uppercase tracking-wider font-medium text-neutral-400">
                          {CATEGORY_LABELS[insight.category] || insight.category}
                        </span>
                      </div>
                      <p className="text-sm text-neutral-600 mt-1">{insight.body}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
