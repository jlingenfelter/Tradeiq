"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useWealthDashboard } from "@/hooks/use-wealth";
import type { WarningSeverity } from "@/types";

const SEVERITY_ORDER: WarningSeverity[] = ["critical", "high", "medium", "info"];

function severityVariant(severity: string) {
  switch (severity) {
    case "critical": return "destructive" as const;
    case "high": return "destructive" as const;
    case "medium": return "warning" as const;
    default: return "info" as const;
  }
}

export default function WarningsPage() {
  const { data: dashboard, isLoading } = useWealthDashboard();
  const [filter, setFilter] = useState<string | undefined>();

  const warnings = dashboard?.top_warnings || [];
  const filtered = filter ? warnings.filter((w) => w.severity === filter) : warnings;

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Warnings</h2>
          <p className="text-sm text-neutral-500">Risk alerts and issues across your wealth</p>
        </div>

        {/* Severity Filter */}
        <div className="flex gap-2">
          <Button
            variant={filter === undefined ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(undefined)}
          >
            All ({warnings.length})
          </Button>
          {SEVERITY_ORDER.map((s) => {
            const count = warnings.filter((w) => w.severity === s).length;
            if (count === 0) return null;
            return (
              <Button
                key={s}
                variant={filter === s ? "default" : "outline"}
                size="sm"
                onClick={() => setFilter(s)}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)} ({count})
              </Button>
            );
          })}
        </div>

        {isLoading ? (
          <div className="text-neutral-500">Loading warnings...</div>
        ) : filtered.length > 0 ? (
          <div className="space-y-3">
            {filtered.map((w, i) => (
              <Card key={i}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <Badge variant={severityVariant(w.severity)} className="mt-0.5 shrink-0">
                      {w.severity}
                    </Badge>
                    <div className="flex-1">
                      <div className="font-medium">{w.title}</div>
                      <div className="text-sm text-neutral-500 mt-1">{w.description}</div>
                      {w.warning_type && (
                        <div className="mt-2">
                          <span className="text-xs bg-neutral-100 rounded px-2 py-1">
                            {w.warning_type.replace(/_/g, " ")}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-neutral-500">No warnings detected. Your wealth profile looks balanced.</div>
        )}
      </div>
    </AppShell>
  );
}
