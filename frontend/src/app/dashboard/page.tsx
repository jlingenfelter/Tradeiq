"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { PortfolioValueCard } from "@/components/dashboard/PortfolioValueCard";
import { HealthScoreCard } from "@/components/dashboard/HealthScoreCard";
import { TopRisksCard } from "@/components/dashboard/TopRisksCard";
import { TopHoldingsCard } from "@/components/dashboard/TopHoldingsCard";
import { SectorExposureChart } from "@/components/dashboard/SectorExposureChart";
import { CountryExposureChart } from "@/components/dashboard/CountryExposureChart";
import { AiSummaryPanel } from "@/components/dashboard/AiSummaryPanel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { usePortfolios, useUpdatePortfolio, useDeletePortfolio } from "@/hooks/use-portfolio";
import { useDashboard, useRecomputeAnalytics } from "@/hooks/use-analytics";
import { RefreshCw, Pencil, Trash2, Plus, X, Check } from "lucide-react";
import type { HealthScoreBreakdown } from "@/types";

export default function DashboardPage() {
  const router = useRouter();
  const { data: portfolios, isLoading: loadingPortfolios } = usePortfolios();
  const [activePortfolioId, setActivePortfolioId] = useState<string>("");
  const [showManage, setShowManage] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const updatePortfolio = useUpdatePortfolio();
  const deletePortfolio = useDeletePortfolio();

  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !activePortfolioId) {
      setActivePortfolioId(portfolios[0].id);
    }
    if (portfolios && portfolios.length === 0 && !loadingPortfolios) {
      router.push("/onboarding");
    }
  }, [portfolios, activePortfolioId, loadingPortfolios, router]);

  // If active portfolio was deleted, switch to first available
  useEffect(() => {
    if (portfolios && portfolios.length > 0 && activePortfolioId) {
      const exists = portfolios.some((p) => p.id === activePortfolioId);
      if (!exists) {
        setActivePortfolioId(portfolios[0].id);
      }
    }
  }, [portfolios, activePortfolioId]);

  const { data: dashboard, isLoading, isError, refetch } = useDashboard(activePortfolioId);
  const recompute = useRecomputeAnalytics(activePortfolioId);

  function handleRefresh() {
    recompute.mutate(undefined, {
      onSuccess: () => {
        setTimeout(() => refetch(), 3000);
      },
    });
  }

  function handleStartEdit(id: string, name: string) {
    setEditingId(id);
    setEditName(name);
  }

  function handleSaveEdit(id: string) {
    updatePortfolio.mutate({ id, name: editName }, {
      onSuccess: () => setEditingId(null),
    });
  }

  function handleDelete(id: string, name: string) {
    if (confirm(`Delete "${name}"? This will remove all positions in this portfolio.`)) {
      deletePortfolio.mutate(id);
    }
  }

  if (loadingPortfolios || !activePortfolioId) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64">
          <div className="text-neutral-500">Loading portfolios...</div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">{dashboard?.portfolio_name || "Dashboard"}</h2>
            <p className="text-sm text-neutral-500">Portfolio overview and key metrics</p>
          </div>
          <div className="flex items-center gap-2">
            {portfolios && portfolios.length > 1 && (
              <select
                className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
                value={activePortfolioId}
                onChange={(e) => setActivePortfolioId(e.target.value)}
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            )}
            <Button variant="outline" size="sm" onClick={() => setShowManage(!showManage)}>
              <Pencil className="h-4 w-4 mr-1" />
              Manage
            </Button>
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={recompute.isPending}>
              <RefreshCw className={`h-4 w-4 mr-1 ${recompute.isPending ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Portfolio Management Panel */}
        {showManage && portfolios && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Manage Portfolios</CardTitle>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => router.push("/onboarding")}>
                    <Plus className="h-4 w-4 mr-1" />
                    New Portfolio
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowManage(false)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {portfolios.map((p) => (
                  <div key={p.id} className="flex items-center gap-2 rounded-md border px-3 py-2">
                    {editingId === p.id ? (
                      <>
                        <Input
                          value={editName}
                          onChange={(e) => setEditName(e.target.value)}
                          className="flex-1 h-8"
                          autoFocus
                          onKeyDown={(e) => e.key === "Enter" && handleSaveEdit(p.id)}
                        />
                        <Button size="sm" variant="ghost" onClick={() => handleSaveEdit(p.id)} disabled={updatePortfolio.isPending}>
                          <Check className="h-4 w-4 text-green-600" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                          <X className="h-4 w-4" />
                        </Button>
                      </>
                    ) : (
                      <>
                        <span className="flex-1 text-sm font-medium">{p.name}</span>
                        <span className="text-xs text-neutral-400">{p.id === activePortfolioId ? "Active" : ""}</span>
                        <Button size="sm" variant="ghost" onClick={() => handleStartEdit(p.id, p.name)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDelete(p.id, p.name)}>
                          <Trash2 className="h-3.5 w-3.5 text-red-500" />
                        </Button>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-neutral-500">Computing analytics...</div>
          </div>
        ) : isError ? (
          <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
            Failed to load dashboard data. Try refreshing.
          </div>
        ) : dashboard ? (
          <>
            {/* Top row: Value + Health Score */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <PortfolioValueCard
                totalValue={dashboard.total_value}
                dailyChange={dashboard.daily_change}
                dailyChangePct={dashboard.daily_change_pct}
                currency={dashboard.base_currency}
              />
              <HealthScoreCard
                score={dashboard.health_score}
                breakdown={dashboard.health_score_breakdown as HealthScoreBreakdown}
              />
            </div>

            {/* Risks + Holdings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TopRisksCard risks={dashboard.top_risks} />
              <TopHoldingsCard holdings={dashboard.top_holdings} />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SectorExposureChart data={dashboard.sector_exposure} />
              <CountryExposureChart data={dashboard.country_exposure} />
            </div>

            {/* AI Summary */}
            <AiSummaryPanel summary={dashboard.ai_summary} portfolioId={activePortfolioId} />
          </>
        ) : null}
      </div>
    </AppShell>
  );
}
