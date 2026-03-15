"use client";

import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";
import type { WealthDashboardResponse } from "@/types";
import {
  DollarSign, Droplets, Building2, Bitcoin,
  Briefcase, PiggyBank, TrendingDown,
} from "lucide-react";

interface Props {
  data: WealthDashboardResponse;
}

export function WealthSummaryCards({ data }: Props) {
  const cards = [
    { label: "Liquid Assets", value: data.liquid_assets, icon: Droplets, color: "text-blue-600" },
    { label: "Cash", value: data.cash_value, icon: DollarSign, color: "text-green-600" },
    { label: "Investments", value: data.investment_value, icon: TrendingDown, color: "text-indigo-600" },
    { label: "Property", value: data.property_value, icon: Building2, color: "text-orange-600" },
    { label: "Crypto", value: data.crypto_value, icon: Bitcoin, color: "text-yellow-600" },
    { label: "Business", value: data.business_value, icon: Briefcase, color: "text-purple-600" },
    { label: "Pensions", value: data.pension_value, icon: PiggyBank, color: "text-teal-600" },
    { label: "Liabilities", value: data.total_liabilities, icon: TrendingDown, color: "text-red-600" },
  ].filter((c) => c.value > 0 || c.label === "Liabilities");

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((card) => (
        <Card key={card.label}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <card.icon className={`h-4 w-4 ${card.color}`} />
              <span className="text-xs text-neutral-500">{card.label}</span>
            </div>
            <p className="text-lg font-semibold">
              {formatCurrency(card.value, data.base_currency)}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
