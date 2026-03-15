"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { useNetWorthHistory } from "@/hooks/use-wealth";
import { formatCurrency } from "@/lib/utils";

export function NetWorthChart() {
  const { data, isLoading } = useNetWorthHistory();

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Net Worth Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center text-neutral-400 text-sm">
            Loading history...
          </div>
        </CardContent>
      </Card>
    );
  }

  const history = data?.history ?? [];

  if (history.length < 2) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Net Worth Over Time</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-72 flex items-center justify-center text-neutral-400 text-sm">
            Not enough data yet. Your chart will appear after a few snapshots.
          </div>
        </CardContent>
      </Card>
    );
  }

  const chartData = history.map((item) => ({
    date: new Date(item.date).toLocaleDateString("en-GB", { day: "numeric", month: "short" }),
    "Net Worth": item.net_worth,
    "Assets": item.total_assets,
    "Liabilities": item.total_liabilities,
  }));

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Net Worth Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="netWorthGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="assetsGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#9ca3af" }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#9ca3af" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) =>
                  v >= 1_000_000 ? `${(v / 1_000_000).toFixed(1)}M`
                  : v >= 1_000 ? `${(v / 1_000).toFixed(0)}k`
                  : String(v)
                }
                width={55}
              />
              <Tooltip
                formatter={(value: number) => formatCurrency(value)}
                labelStyle={{ fontWeight: 600, marginBottom: 4 }}
                contentStyle={{
                  borderRadius: 8, border: "1px solid #e5e7eb",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                }}
              />
              <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
              <Area
                type="monotone"
                dataKey="Assets"
                stroke="#10b981"
                fill="url(#assetsGrad)"
                strokeWidth={1.5}
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="Liabilities"
                stroke="#ef4444"
                fill="none"
                strokeWidth={1.5}
                strokeDasharray="4 3"
                dot={false}
              />
              <Area
                type="monotone"
                dataKey="Net Worth"
                stroke="#6366f1"
                fill="url(#netWorthGrad)"
                strokeWidth={2.5}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
