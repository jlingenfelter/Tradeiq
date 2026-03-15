"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { useNetWorthHistory } from "@/hooks/use-wealth";
import { formatCurrency } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

export default function HistoryPage() {
  const { data, isLoading } = useNetWorthHistory();
  const history = data?.history || [];

  const chartData = history.map((h) => ({
    date: new Date(h.date).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    "Net Worth": h.net_worth,
    "Total Assets": h.total_assets,
    "Liabilities": h.total_liabilities,
    "Liquid Assets": h.liquid_assets,
  }));

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Performance & History</h2>
          <p className="text-sm text-neutral-500">Track your wealth over time</p>
        </div>

        {isLoading ? (
          <div className="text-neutral-500">Loading history...</div>
        ) : history.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-neutral-500">
              No snapshots yet. Your wealth history will build as you use the platform.
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Net worth over time */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Net Worth Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                      <Tooltip formatter={(value) => formatCurrency(Number(value))} />
                      <Legend />
                      <Line type="monotone" dataKey="Net Worth" stroke="#3b82f6" strokeWidth={2} dot={false} />
                      <Line type="monotone" dataKey="Total Assets" stroke="#10b981" strokeWidth={1} strokeDasharray="5 5" dot={false} />
                      <Line type="monotone" dataKey="Liabilities" stroke="#ef4444" strokeWidth={1} strokeDasharray="5 5" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Snapshot table */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Recent Snapshots</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="px-4 py-3 text-xs font-medium text-neutral-500">Date</th>
                      <th className="px-4 py-3 text-xs font-medium text-neutral-500 text-right">Assets</th>
                      <th className="px-4 py-3 text-xs font-medium text-neutral-500 text-right">Liabilities</th>
                      <th className="px-4 py-3 text-xs font-medium text-neutral-500 text-right">Net Worth</th>
                      <th className="px-4 py-3 text-xs font-medium text-neutral-500 text-right">Liquid</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...history].reverse().slice(0, 20).map((h, i) => (
                      <tr key={i} className="border-b last:border-0 hover:bg-neutral-50">
                        <td className="px-4 py-3 text-sm">{new Date(h.date).toLocaleDateString()}</td>
                        <td className="px-4 py-3 text-sm text-right">{formatCurrency(h.total_assets)}</td>
                        <td className="px-4 py-3 text-sm text-right text-red-600">{formatCurrency(h.total_liabilities)}</td>
                        <td className="px-4 py-3 text-sm text-right font-medium">{formatCurrency(h.net_worth)}</td>
                        <td className="px-4 py-3 text-sm text-right text-blue-600">{formatCurrency(h.liquid_assets)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AppShell>
  );
}
