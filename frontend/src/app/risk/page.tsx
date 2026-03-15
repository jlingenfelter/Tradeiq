"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useDashboard } from "@/hooks/use-analytics";
import { formatCurrency } from "@/lib/utils";

export default function RiskPage() {
  const { data: portfolios } = usePortfolios();
  const [portfolioId, setPortfolioId] = useState("");

  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !portfolioId) {
      setPortfolioId(portfolios[0].id);
    }
  }, [portfolios, portfolioId]);

  const { data: dashboard, isLoading } = useDashboard(portfolioId);

  function concentrationBadge(value: number, thresholds: number[]) {
    if (value >= thresholds[3]) return <Badge variant="destructive">{value.toFixed(1)}%</Badge>;
    if (value >= thresholds[2]) return <Badge variant="destructive">{value.toFixed(1)}%</Badge>;
    if (value >= thresholds[1]) return <Badge variant="warning">{value.toFixed(1)}%</Badge>;
    if (value >= thresholds[0]) return <Badge variant="info">{value.toFixed(1)}%</Badge>;
    return <Badge variant="success">{value.toFixed(1)}%</Badge>;
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Risk Analysis</h2>
          <p className="text-sm text-neutral-500">Concentration metrics and stress scenarios</p>
        </div>

        {isLoading ? (
          <div className="text-neutral-500">Loading risk analysis...</div>
        ) : dashboard ? (
          <>
            {/* Concentration Metrics */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Concentration Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-1">
                    <div className="text-sm text-neutral-500">Top Holding</div>
                    <div className="text-lg font-semibold flex items-center gap-2">
                      {dashboard.top_holdings[0]?.symbol || "—"}
                      {dashboard.health_score_breakdown && concentrationBadge(
                        dashboard.top_holdings[0]?.weight || 0, [10, 15, 20, 25]
                      )}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-sm text-neutral-500">Top 3 Holdings</div>
                    <div className="text-lg font-semibold">
                      {concentrationBadge(
                        dashboard.top_holdings.slice(0, 3).reduce((s, h) => s + h.weight, 0),
                        [35, 45, 55, 65]
                      )}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-sm text-neutral-500">Top Sector</div>
                    <div className="text-lg font-semibold flex items-center gap-2">
                      {dashboard.sector_exposure[0]?.sector || "—"}
                      {concentrationBadge(dashboard.sector_exposure[0]?.weight || 0, [30, 40, 50, 60])}
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-sm text-neutral-500">Top Country</div>
                    <div className="text-lg font-semibold flex items-center gap-2">
                      {dashboard.country_exposure[0]?.country || "—"}
                      {concentrationBadge(dashboard.country_exposure[0]?.weight || 0, [50, 60, 70, 80])}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Stress Tests */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Stress Scenarios</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {(dashboard.stress_tests || []).map((test, i) => (
                    <div key={i} className="border-b last:border-0 pb-4 last:pb-0">
                      <div className="flex items-center justify-between">
                        <div className="font-medium text-sm">{test.scenario}</div>
                        <div className="text-right">
                          <span className="text-red-600 font-semibold">
                            {test.portfolio_impact_pct}%
                          </span>
                          <span className="text-xs text-neutral-500 ml-2">
                            ({formatCurrency(Math.abs(test.portfolio_impact_value))})
                          </span>
                        </div>
                      </div>
                      {test.top_contributors && (
                        <div className="mt-2 flex gap-2 flex-wrap">
                          {test.top_contributors.map((c: { symbol: string; impact: number }, j: number) => (
                            <span key={j} className="text-xs bg-neutral-100 rounded px-2 py-1">
                              {c.symbol}: {formatCurrency(Math.abs(c.impact))}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
