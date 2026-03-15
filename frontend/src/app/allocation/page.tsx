"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useWealthDashboard, useWealthAllocation } from "@/hooks/use-wealth";
import { formatCurrency } from "@/lib/utils";
import { WealthAllocationChart } from "@/components/wealth/WealthAllocationChart";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const LIQUIDITY_COLORS: Record<string, string> = {
  highly_liquid: "#10b981",
  liquid: "#3b82f6",
  semi_liquid: "#f59e0b",
  illiquid: "#ef4444",
};

const LIQUIDITY_LABELS: Record<string, string> = {
  highly_liquid: "Highly Liquid",
  liquid: "Liquid",
  semi_liquid: "Semi-Liquid",
  illiquid: "Illiquid",
};

interface AllocationData {
  liquidity_allocation?: Record<string, number>;
  debt_to_asset_ratio?: number;
  debt_to_net_worth_ratio?: number;
  property_ltv?: number;
}

export default function AllocationPage() {
  const { data: dashboard } = useWealthDashboard();
  const { data: rawAllocation } = useWealthAllocation();
  const allocation = rawAllocation as AllocationData | undefined;

  if (!dashboard) {
    return (
      <AppShell>
        <div className="text-neutral-500">Loading allocation data...</div>
      </AppShell>
    );
  }

  const liquidityData = Object.entries(allocation?.liquidity_allocation || {}).map(
    ([key, value]) => ({
      name: LIQUIDITY_LABELS[key] || key,
      value: value,
      color: LIQUIDITY_COLORS[key] || "#94a3b8",
    })
  ).filter((d) => d.value > 0);

  const debtToAsset = allocation?.debt_to_asset_ratio || 0;
  const debtToNetWorth = allocation?.debt_to_net_worth_ratio || 0;
  const propertyLtv = allocation?.property_ltv || 0;

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Allocation & Risk</h2>
          <p className="text-sm text-neutral-500">Asset allocation, liquidity, and leverage analysis</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <WealthAllocationChart allocation={dashboard.allocation} currency={dashboard.base_currency} />

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Liquidity Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={liquidityData} layout="vertical">
                    <XAxis type="number" tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(value) => formatCurrency(Number(value), dashboard.base_currency)} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {liquidityData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Key ratios */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-neutral-500 mb-1">Debt-to-Asset Ratio</p>
              <p className={`text-2xl font-bold ${debtToAsset > 40 ? "text-red-600" : debtToAsset > 25 ? "text-yellow-600" : "text-green-600"}`}>
                {debtToAsset.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-neutral-500 mb-1">Debt-to-Net-Worth Ratio</p>
              <p className={`text-2xl font-bold ${debtToNetWorth > 50 ? "text-red-600" : debtToNetWorth > 30 ? "text-yellow-600" : "text-green-600"}`}>
                {debtToNetWorth.toFixed(1)}%
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs text-neutral-500 mb-1">Property LTV</p>
              <p className={`text-2xl font-bold ${propertyLtv > 80 ? "text-red-600" : propertyLtv > 60 ? "text-yellow-600" : "text-green-600"}`}>
                {propertyLtv > 0 ? `${propertyLtv.toFixed(1)}%` : "N/A"}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Liquid vs Illiquid summary */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Wealth Composition</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-neutral-500">Liquid Assets</p>
                <p className="text-lg font-semibold text-blue-600">
                  {formatCurrency(dashboard.liquid_assets, dashboard.base_currency)}
                </p>
                <p className="text-xs text-neutral-400">
                  {dashboard.total_assets > 0 ? `${(dashboard.liquid_assets / dashboard.total_assets * 100).toFixed(1)}% of assets` : ""}
                </p>
              </div>
              <div>
                <p className="text-xs text-neutral-500">Illiquid Assets</p>
                <p className="text-lg font-semibold text-orange-600">
                  {formatCurrency(dashboard.illiquid_assets, dashboard.base_currency)}
                </p>
                <p className="text-xs text-neutral-400">
                  {dashboard.total_assets > 0 ? `${(dashboard.illiquid_assets / dashboard.total_assets * 100).toFixed(1)}% of assets` : ""}
                </p>
              </div>
              <div>
                <p className="text-xs text-neutral-500">Liquid Net Worth</p>
                <p className={`text-lg font-semibold ${dashboard.liquid_net_worth >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {formatCurrency(dashboard.liquid_net_worth, dashboard.base_currency)}
                </p>
              </div>
              <div>
                <p className="text-xs text-neutral-500">Total Liabilities</p>
                <p className="text-lg font-semibold text-red-600">
                  {formatCurrency(dashboard.total_liabilities, dashboard.base_currency)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
