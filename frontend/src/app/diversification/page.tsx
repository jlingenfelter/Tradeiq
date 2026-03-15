"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useDashboard, useAnalyticsLatest } from "@/hooks/use-analytics";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

const COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
];

export default function DiversificationPage() {
  const { data: portfolios } = usePortfolios();
  const [portfolioId, setPortfolioId] = useState("");

  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !portfolioId) {
      setPortfolioId(portfolios[0].id);
    }
  }, [portfolios, portfolioId]);

  const { data: dashboard, isLoading } = useDashboard(portfolioId);
  const { data: analytics } = useAnalyticsLatest(portfolioId);

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Diversification</h2>
          <p className="text-sm text-neutral-500">Portfolio spread analysis and benchmark comparison</p>
        </div>

        {isLoading ? (
          <div className="text-neutral-500">Loading...</div>
        ) : dashboard ? (
          <>
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-neutral-500">Positions</div>
                  <div className="text-2xl font-bold">{analytics?.position_count || dashboard.top_holdings.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-neutral-500">Sectors</div>
                  <div className="text-2xl font-bold">{dashboard.sector_exposure.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-neutral-500">Countries</div>
                  <div className="text-2xl font-bold">{dashboard.country_exposure.length}</div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-neutral-500">HHI Index</div>
                  <div className="text-2xl font-bold">{analytics?.hhi?.toFixed(3) || "—"}</div>
                </CardContent>
              </Card>
            </div>

            {/* Sector Spread */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader><CardTitle className="text-base">Sector Spread</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={dashboard.sector_exposure.map((s) => ({ name: s.sector, value: s.weight }))}
                        cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                        paddingAngle={2} dataKey="value"
                      >
                        {dashboard.sector_exposure.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => `${Number(v).toFixed(1)}%`} />
                      <Legend formatter={(v: string) => <span className="text-xs">{v}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle className="text-base">Country Spread</CardTitle></CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={dashboard.country_exposure.map((c) => ({ name: c.country, value: c.weight }))}
                        cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                        paddingAngle={2} dataKey="value"
                      >
                        {dashboard.country_exposure.map((_, i) => (
                          <Cell key={i} fill={COLORS[i % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v) => `${Number(v).toFixed(1)}%`} />
                      <Legend formatter={(v: string) => <span className="text-xs">{v}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Benchmark Comparison */}
            {analytics?.benchmark_comparison && Array.isArray(analytics.benchmark_comparison) && analytics.benchmark_comparison.length > 0 && (
              <Card>
                <CardHeader><CardTitle className="text-base">Benchmark Comparison (vs S&P 500)</CardTitle></CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {(analytics.benchmark_comparison as Array<{ sector: string; portfolio_weight: number; benchmark_weight: number; difference: number }>).map((item) => (
                      <div key={item.sector} className="flex items-center gap-3 text-sm">
                        <div className="w-40 truncate">{item.sector}</div>
                        <div className="flex-1 flex items-center gap-2">
                          <div className="w-16 text-right text-neutral-500">{item.portfolio_weight.toFixed(1)}%</div>
                          <div className="flex-1 h-4 bg-neutral-100 rounded relative overflow-hidden">
                            <div
                              className="absolute top-0 h-full bg-blue-500 opacity-40"
                              style={{ width: `${Math.min(item.benchmark_weight, 100)}%` }}
                            />
                            <div
                              className="absolute top-0 h-full bg-blue-500"
                              style={{ width: `${Math.min(item.portfolio_weight, 100)}%` }}
                            />
                          </div>
                          <div className={`w-16 text-right font-medium ${item.difference > 0 ? "text-blue-600" : "text-neutral-500"}`}>
                            {item.difference > 0 ? "+" : ""}{item.difference.toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 flex gap-4 text-xs text-neutral-400">
                    <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 rounded" /> Portfolio</span>
                    <span className="flex items-center gap-1"><span className="w-3 h-3 bg-blue-500 opacity-40 rounded" /> S&P 500</span>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
