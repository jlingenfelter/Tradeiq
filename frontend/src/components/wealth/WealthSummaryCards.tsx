"use client";

import { Card, CardContent } from "@/components/ui/card";
import { AnimatedCounter } from "@/components/ui/animated-counter";
import type { WealthDashboardResponse } from "@/types";
import {
  DollarSign, Droplets, Building2, Bitcoin,
  Briefcase, PiggyBank, TrendingDown, TrendingUp,
  ArrowUpRight, ArrowDownRight,
} from "lucide-react";

interface Props {
  data: WealthDashboardResponse;
}

const iconBg: Record<string, string> = {
  "text-blue-600": "bg-blue-100",
  "text-green-600": "bg-green-100",
  "text-indigo-600": "bg-indigo-100",
  "text-orange-600": "bg-orange-100",
  "text-yellow-600": "bg-yellow-100",
  "text-purple-600": "bg-purple-100",
  "text-teal-600": "bg-teal-100",
  "text-red-600": "bg-red-100",
};

const borderColors: Record<string, string> = {
  "text-blue-600": "border-l-blue-500",
  "text-green-600": "border-l-green-500",
  "text-indigo-600": "border-l-indigo-500",
  "text-orange-600": "border-l-orange-500",
  "text-yellow-600": "border-l-yellow-500",
  "text-purple-600": "border-l-purple-500",
  "text-teal-600": "border-l-teal-500",
  "text-red-600": "border-l-red-500",
};

export function WealthSummaryCards({ data }: Props) {
  const cards = [
    { label: "Liquid Assets", value: data.liquid_assets, icon: Droplets, color: "text-blue-600" },
    { label: "Cash", value: data.cash_value, icon: DollarSign, color: "text-green-600" },
    { label: "Investments", value: data.investment_value, icon: TrendingUp, color: "text-indigo-600" },
    { label: "Property", value: data.property_value, icon: Building2, color: "text-orange-600" },
    { label: "Crypto", value: data.crypto_value, icon: Bitcoin, color: "text-yellow-600" },
    { label: "Business", value: data.business_value, icon: Briefcase, color: "text-purple-600" },
    { label: "Pensions", value: data.pension_value, icon: PiggyBank, color: "text-teal-600" },
    { label: "Liabilities", value: data.total_liabilities, icon: TrendingDown, color: "text-red-600" },
  ].filter((c) => c.value > 0 || c.label === "Liabilities");

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {cards.map((card, i) => (
        <Card
          key={card.label}
          className={`card-hover border-l-4 ${borderColors[card.color] || "border-l-slate-300"} animate-fade-in-up`}
          style={{ animationDelay: `${i * 60}ms` }}
        >
          <CardContent className="p-4">
            <div className="flex items-center gap-2.5 mb-3">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full ${iconBg[card.color] || "bg-slate-100"}`}>
                <card.icon className={`h-4 w-4 ${card.color}`} />
              </div>
              <span className="text-xs font-medium text-neutral-500">{card.label}</span>
            </div>
            <p className="text-lg font-bold tracking-tight">
              <AnimatedCounter
                value={card.value}
                prefix={data.base_currency === "USD" ? "$" : data.base_currency + " "}
                duration={1000 + i * 100}
              />
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
