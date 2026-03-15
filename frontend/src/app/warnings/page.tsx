"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useWarnings } from "@/hooks/use-analytics";
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
  const { data: portfolios } = usePortfolios();
  const [portfolioId, setPortfolioId] = useState("");
  const [filter, setFilter] = useState<string | undefined>();

  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !portfolioId) {
      setPortfolioId(portfolios[0].id);
    }
  }, [portfolios, portfolioId]);

  const { data: warnings, isLoading } = useWarnings(portfolioId, filter);

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Warnings</h2>
          <p className="text-sm text-neutral-500">Portfolio risk alerts and issues</p>
        </div>

        {/* Severity Filter */}
        <div className="flex gap-2">
          <Button
            variant={filter === undefined ? "default" : "outline"}
            size="sm"
            onClick={() => setFilter(undefined)}
          >
            All
          </Button>
          {SEVERITY_ORDER.map((s) => (
            <Button
              key={s}
              variant={filter === s ? "default" : "outline"}
              size="sm"
              onClick={() => setFilter(s)}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </Button>
          ))}
        </div>

        {isLoading ? (
          <div className="text-neutral-500">Loading warnings...</div>
        ) : warnings && warnings.length > 0 ? (
          <div className="space-y-3">
            {warnings.map((w) => (
              <Card key={w.id}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <Badge variant={severityVariant(w.severity)} className="mt-0.5 shrink-0">
                      {w.severity}
                    </Badge>
                    <div className="flex-1">
                      <div className="font-medium">{w.title}</div>
                      <div className="text-sm text-neutral-500 mt-1">{w.description}</div>
                      {w.evidence_json && Object.keys(w.evidence_json).length > 0 && (
                        <div className="mt-2 flex gap-2 flex-wrap">
                          {Object.entries(w.evidence_json).map(([key, val]) => (
                            <span key={key} className="text-xs bg-neutral-100 rounded px-2 py-1">
                              {key}: {typeof val === "number" ? val.toFixed?.(2) ?? val : String(val)}
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="text-xs text-neutral-400 mt-2">
                        {new Date(w.triggered_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-neutral-500">No warnings detected. Your portfolio looks balanced.</div>
        )}
      </div>
    </AppShell>
  );
}
