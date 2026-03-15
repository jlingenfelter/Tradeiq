"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useWealthDashboard } from "@/hooks/use-wealth";
import { formatCurrency } from "@/lib/utils";
import { WealthAllocationChart } from "@/components/wealth/WealthAllocationChart";
import { WealthHealthCard } from "@/components/wealth/WealthHealthCard";
import { WealthSummaryCards } from "@/components/wealth/WealthSummaryCards";
import { WealthAiSummary } from "@/components/wealth/WealthAiSummary";
import { WeeklyRecapCard } from "@/components/wealth/WeeklyRecapCard";
import { GoalProgressCard } from "@/components/wealth/GoalProgressCard";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export default function OverviewPage() {
  const { data, isLoading } = useWealthDashboard();

  if (isLoading) {
    return (
      <AppShell>
        <div className="text-neutral-500">Loading wealth overview...</div>
      </AppShell>
    );
  }

  if (!data || data.total_assets === 0) {
    return (
      <AppShell>
        <div className="max-w-xl mx-auto text-center py-20 space-y-4">
          <h2 className="text-2xl font-bold">Welcome to Wealth Copilot</h2>
          <p className="text-neutral-500">
            Start by adding your assets and liabilities to see your full wealth picture.
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/assets">
              <Button>Add Assets</Button>
            </Link>
            <Link href="/liabilities">
              <Button variant="outline">Add Liabilities</Button>
            </Link>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Wealth Overview</h2>
          <p className="text-sm text-neutral-500">
            Your complete financial picture at a glance
          </p>
        </div>

        {/* Net Worth Hero */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-baseline justify-between">
              <div>
                <p className="text-sm text-neutral-500 mb-1">Net Worth</p>
                <p className="text-3xl font-bold">
                  {formatCurrency(data.net_worth, data.base_currency)}
                </p>
                {data.net_worth_change_30d !== null && (
                  <p className={`text-sm mt-1 ${data.net_worth_change_30d >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {data.net_worth_change_30d >= 0 ? "+" : ""}
                    {formatCurrency(data.net_worth_change_30d, data.base_currency)} since last snapshot
                  </p>
                )}
              </div>
              <div className="text-right space-y-1">
                <div className="text-sm">
                  <span className="text-neutral-500">Assets </span>
                  <span className="font-medium">{formatCurrency(data.total_assets, data.base_currency)}</span>
                </div>
                <div className="text-sm">
                  <span className="text-neutral-500">Liabilities </span>
                  <span className="font-medium text-red-600">{formatCurrency(data.total_liabilities, data.base_currency)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Summary cards */}
        <WealthSummaryCards data={data} />

        {/* Goals + Weekly Recap */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <GoalProgressCard />
          <WeeklyRecapCard />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Allocation chart */}
          <WealthAllocationChart allocation={data.allocation} currency={data.base_currency} />

          {/* Health score */}
          <WealthHealthCard
            score={data.health_score}
            breakdown={data.health_score_breakdown}
          />
        </div>

        {/* Top Warnings */}
        {data.top_warnings.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Top Issues</CardTitle>
                <Link href="/warnings" className="text-xs text-neutral-500 hover:text-neutral-900 flex items-center gap-1">
                  View all <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.top_warnings.map((w, i) => (
                  <div key={i} className="flex items-start gap-3 rounded-md border px-4 py-3">
                    <Badge variant={w.severity === "critical" || w.severity === "high" ? "destructive" : "secondary"} className="mt-0.5">
                      {w.severity}
                    </Badge>
                    <div>
                      <div className="text-sm font-medium">{w.title}</div>
                      <div className="text-xs text-neutral-500">{w.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Top Concentrations */}
        {data.top_concentrations.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Top Concentrations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {data.top_concentrations.map((c, i) => (
                  <div key={i} className="flex items-center justify-between py-2">
                    <span className="text-sm font-medium">{c.label}</span>
                    <div className="text-right">
                      <span className="text-sm font-medium">
                        {formatCurrency(c.value, data.base_currency)}
                      </span>
                      <span className="text-xs text-neutral-500 ml-2">
                        {c.weight_of_assets.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Holdings Breakdown */}
        {data.holdings && data.holdings.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">All Holdings</CardTitle>
                <span className="text-xs text-neutral-500">{data.holdings.length} items</span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-neutral-500">
                      <th className="pb-2 font-medium">Name</th>
                      <th className="pb-2 font-medium">Category</th>
                      <th className="pb-2 font-medium text-right">Value</th>
                      <th className="pb-2 font-medium text-right">Weight</th>
                      <th className="pb-2 font-medium">Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.holdings.map((h, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-2.5">
                          <div className="font-medium">{h.name}</div>
                          {h.symbol && (
                            <div className="text-xs text-neutral-400">{h.symbol}</div>
                          )}
                        </td>
                        <td className="py-2.5">
                          <Badge variant="secondary" className="text-xs font-normal">
                            {h.category}
                          </Badge>
                        </td>
                        <td className="py-2.5 text-right font-medium">
                          {formatCurrency(h.value, data.base_currency)}
                        </td>
                        <td className="py-2.5 text-right text-neutral-500">
                          {h.weight.toFixed(1)}%
                        </td>
                        <td className="py-2.5">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${
                            h.source === "portfolio"
                              ? "bg-indigo-50 text-indigo-700"
                              : "bg-neutral-100 text-neutral-600"
                          }`}>
                            {h.source === "portfolio" ? "Broker" : "Manual"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* AI Summary */}
        <WealthAiSummary />
      </div>
    </AppShell>
  );
}
