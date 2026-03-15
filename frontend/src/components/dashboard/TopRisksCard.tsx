"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Risk {
  warning_type?: string;
  type?: string;
  severity: string;
  title: string;
  description: string;
}

interface Props {
  risks: Risk[];
}

function severityVariant(severity: string) {
  switch (severity) {
    case "critical": return "destructive" as const;
    case "high": return "destructive" as const;
    case "medium": return "warning" as const;
    default: return "info" as const;
  }
}

export function TopRisksCard({ risks }: Props) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Top Risks</CardTitle>
      </CardHeader>
      <CardContent>
        {risks.length === 0 ? (
          <p className="text-sm text-neutral-500">No significant risks detected</p>
        ) : (
          <div className="space-y-3">
            {risks.map((risk, i) => (
              <div key={i} className="flex items-start gap-3">
                <Badge variant={severityVariant(risk.severity)} className="mt-0.5 shrink-0">
                  {risk.severity}
                </Badge>
                <div>
                  <div className="text-sm font-medium">{risk.title}</div>
                  <div className="text-xs text-neutral-500">{risk.description}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
