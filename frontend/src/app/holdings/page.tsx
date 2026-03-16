"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { HoldingsTable } from "@/components/holdings/HoldingsTable";
import { EmptyState } from "@/components/ui/empty-state";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useAnalyticsLatest } from "@/hooks/use-analytics";
import { HoldingsSkeleton } from "@/components/ui/skeleton-page";
import { BarChart3 } from "lucide-react";

export default function HoldingsPage() {
  const router = useRouter();
  const { data: portfolios } = usePortfolios();
  const [portfolioId, setPortfolioId] = useState("");

  useEffect(() => {
    if (portfolios && portfolios.length > 0 && !portfolioId) {
      setPortfolioId(portfolios[0].id);
    }
  }, [portfolios, portfolioId]);

  const { data: analytics, isLoading } = useAnalyticsLatest(portfolioId);

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Holdings</h2>
          <p className="text-sm text-neutral-500">All positions in your portfolio</p>
        </div>

        {isLoading ? (
          <HoldingsSkeleton />
        ) : analytics?.holdings ? (
          <HoldingsTable holdings={analytics.holdings} />
        ) : (
          <EmptyState
            icon={BarChart3}
            title="No holdings yet"
            description="Connect a broker or add positions manually to see your holdings here."
            action={{ label: "Connect", href: "/connect" }}
          />
        )}
      </div>
    </AppShell>
  );
}
