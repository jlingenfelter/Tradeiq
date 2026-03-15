"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth";
import { usePortfolios } from "@/hooks/use-portfolio";
import { api } from "@/lib/api";
import type { Portfolio, AlertSubscription } from "@/types";
import { Trash2 } from "lucide-react";

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const { data: portfolios, refetch: refetchPortfolios } = usePortfolios();
  const [alerts, setAlerts] = useState<AlertSubscription[]>([]);
  const [portfolioId, setPortfolioId] = useState("");

  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !portfolioId) {
      setPortfolioId(portfolios[0].id);
    }
  }, [portfolios, portfolioId]);

  useEffect(() => {
    if (portfolioId) {
      api.get<AlertSubscription[]>(`/portfolios/${portfolioId}/alerts`)
        .then(setAlerts)
        .catch(() => {});
    }
  }, [portfolioId]);

  async function handleAddAlert(type: string) {
    if (!portfolioId) return;
    try {
      await api.post(`/portfolios/${portfolioId}/alerts`, {
        alert_type: type,
        channel: "in_app",
      });
      const updated = await api.get<AlertSubscription[]>(`/portfolios/${portfolioId}/alerts`);
      setAlerts(updated);
    } catch {}
  }

  async function handleDeleteAlert(alertId: string) {
    try {
      await api.delete(`/alerts/${alertId}`);
      setAlerts(alerts.filter((a) => a.id !== alertId));
    } catch {}
  }

  async function handleDeletePortfolio(id: string) {
    if (!confirm("Delete this portfolio? This cannot be undone.")) return;
    try {
      await api.delete(`/portfolios/${id}`);
      refetchPortfolios();
    } catch {}
  }

  return (
    <AppShell>
      <div className="max-w-2xl space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Settings</h2>
          <p className="text-sm text-neutral-500">Manage your account and preferences</p>
        </div>

        {/* Account */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label className="text-neutral-500">Email</Label>
              <div className="text-sm font-medium">{user?.email}</div>
            </div>
            <div>
              <Label className="text-neutral-500">Member since</Label>
              <div className="text-sm font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
              </div>
            </div>
            <Button variant="outline" onClick={logout} className="mt-2">
              Sign out
            </Button>
          </CardContent>
        </Card>

        {/* Portfolios */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Portfolios</CardTitle>
            <CardDescription>Manage your portfolios</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {portfolios?.map((p) => (
                <div key={p.id} className="flex items-center justify-between rounded-md border px-4 py-3">
                  <div>
                    <div className="text-sm font-medium">{p.name}</div>
                    <div className="text-xs text-neutral-500">{p.base_currency}</div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleDeletePortfolio(p.id)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Alert Subscriptions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Alert Subscriptions</CardTitle>
            <CardDescription>Get notified about portfolio changes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 mb-4">
              {alerts.map((a) => (
                <div key={a.id} className="flex items-center justify-between rounded-md border px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="text-sm font-medium">{a.alert_type.replace(/_/g, " ")}</div>
                    <Badge variant={a.enabled ? "success" : "secondary"}>
                      {a.enabled ? "Active" : "Paused"}
                    </Badge>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => handleDeleteAlert(a.id)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              ))}
              {alerts.length === 0 && (
                <p className="text-sm text-neutral-500">No alert subscriptions</p>
              )}
            </div>
            <div className="flex gap-2 flex-wrap">
              {["concentration_warning", "health_score_change", "weekly_summary"].map((type) => (
                <Button
                  key={type}
                  variant="outline"
                  size="sm"
                  onClick={() => handleAddAlert(type)}
                  disabled={alerts.some((a) => a.alert_type === type)}
                >
                  + {type.replace(/_/g, " ")}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 leading-relaxed">
              Portfolio Copilot is a read-only portfolio monitoring and analysis tool. It does not
              execute trades, manage portfolios, or provide personalized investment advice. All
              analytics are for informational purposes only. Past performance does not guarantee
              future results. Always consult a qualified financial advisor before making investment
              decisions.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
