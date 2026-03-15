"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useSmartAlerts } from "@/hooks/use-insights";
import { Bell } from "lucide-react";

const SEVERITY_STYLES: Record<string, string> = {
  success: "bg-green-50 border-green-200 text-green-800",
  warning: "bg-amber-50 border-amber-200 text-amber-800",
  info: "bg-blue-50 border-blue-200 text-blue-800",
};

export function SmartAlertsCard() {
  const { data, isLoading } = useSmartAlerts();

  const alerts = data?.alerts ?? [];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-amber-500" />
          <CardTitle className="text-base">Smart Alerts</CardTitle>
          {alerts.length > 0 && (
            <span className="ml-auto text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
              {alerts.length}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-14 rounded-md bg-neutral-100 animate-pulse" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <p className="text-sm text-neutral-400 text-center py-6">
            No alerts right now. Keep tracking and we'll notify you of important changes.
          </p>
        ) : (
          <div className="space-y-2.5">
            {alerts.map((alert, i) => (
              <div
                key={i}
                className={`rounded-lg border px-4 py-3 ${SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.info}`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg leading-none mt-0.5">{alert.icon}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold">{alert.title}</p>
                    <p className="text-xs opacity-80 mt-0.5">{alert.body}</p>
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
