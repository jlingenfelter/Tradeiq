"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useSmartAlerts } from "@/hooks/use-insights";
import { Bell } from "lucide-react";

const SEVERITY_STYLES: Record<string, { card: string; badge: string }> = {
  success: {
    card: "border-green-200 bg-green-50/50",
    badge: "bg-green-100 text-green-700",
  },
  warning: {
    card: "border-amber-200 bg-amber-50/50",
    badge: "bg-amber-100 text-amber-700",
  },
  info: {
    card: "border-blue-200 bg-blue-50/50",
    badge: "bg-blue-100 text-blue-700",
  },
};

export default function AlertsPage() {
  const { data, isLoading } = useSmartAlerts();

  const alerts = data?.alerts ?? [];

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-amber-500" />
            <h2 className="text-2xl font-bold">Smart Alerts</h2>
          </div>
          <p className="text-sm text-neutral-500 mt-1">
            Automated notifications about milestones, changes, and things that need attention.
          </p>
        </div>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 rounded-lg bg-neutral-100 animate-pulse" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-neutral-500">
              No alerts right now. Keep tracking your wealth and we'll notify you of milestones, big changes, and things to review.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert, i) => {
              const style = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.info;
              return (
                <Card key={i} className={`border ${style.card}`}>
                  <CardContent className="p-5">
                    <div className="flex items-start gap-4">
                      <span className="text-2xl">{alert.icon}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold">{alert.title}</p>
                          <span className={`text-[10px] uppercase tracking-wider font-medium px-2 py-0.5 rounded-full ${style.badge}`}>
                            {alert.severity}
                          </span>
                        </div>
                        <p className="text-sm text-neutral-600 mt-1">{alert.body}</p>
                        {alert.timestamp && (
                          <p className="text-xs text-neutral-400 mt-2">
                            {new Date(alert.timestamp).toLocaleDateString("en-GB", {
                              day: "numeric",
                              month: "short",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
