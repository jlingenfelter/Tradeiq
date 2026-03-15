"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { UpgradePrompt } from "@/components/subscription/UpgradePrompt";
import { useSubscription } from "@/hooks/use-subscription";
import { useRunScenario } from "@/hooks/use-scenarios";
import type { ScenarioResult } from "@/hooks/use-scenarios";
import { formatCurrency } from "@/lib/utils";
import {
  Home,
  PiggyBank,
  TrendingUp,
  CreditCard,
  Calculator,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react";
import {
  Area,
  AreaChart,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type ScenarioType = "mortgage_payoff" | "savings_projection" | "asset_change" | "debt_snowball";

interface DebtEntry {
  name: string;
  balance: string;
  rate: string;
  min_payment: string;
}

const SCENARIO_CARDS = [
  {
    type: "mortgage_payoff" as ScenarioType,
    title: "Mortgage Payoff",
    desc: "See how extra payments accelerate your mortgage",
    icon: Home,
  },
  {
    type: "savings_projection" as ScenarioType,
    title: "Savings Projection",
    desc: "Project your savings growth over time",
    icon: PiggyBank,
  },
  {
    type: "asset_change" as ScenarioType,
    title: "Asset Change",
    desc: "Model the impact of asset value changes",
    icon: TrendingUp,
  },
  {
    type: "debt_snowball" as ScenarioType,
    title: "Debt Snowball",
    desc: "Optimize your debt payoff strategy",
    icon: CreditCard,
  },
];

export default function ScenariosPage() {
  const { data: subscription } = useSubscription();
  const tier = subscription?.tier || "free";
  const runScenario = useRunScenario();

  const [selected, setSelected] = useState<ScenarioType | null>(null);
  const [result, setResult] = useState<ScenarioResult | null>(null);

  // Mortgage fields
  const [mortgageBalance, setMortgageBalance] = useState("250000");
  const [mortgageRate, setMortgageRate] = useState("5.5");
  const [mortgagePayment, setMortgagePayment] = useState("1500");
  const [mortgageExtra, setMortgageExtra] = useState("200");

  // Savings fields
  const [savingsCurrent, setSavingsCurrent] = useState("10000");
  const [savingsMonthly, setSavingsMonthly] = useState("500");
  const [savingsReturn, setSavingsReturn] = useState("7");
  const [savingsYears, setSavingsYears] = useState("20");

  // Asset change fields
  const [assetValue, setAssetValue] = useState("500000");
  const [assetChange, setAssetChange] = useState("10");

  // Debt snowball fields
  const [debts, setDebts] = useState<DebtEntry[]>([
    { name: "Credit Card", balance: "5000", rate: "19.9", min_payment: "150" },
    { name: "Car Loan", balance: "12000", rate: "6.5", min_payment: "300" },
  ]);
  const [extraBudget, setExtraBudget] = useState("200");

  function addDebt() {
    setDebts([...debts, { name: "", balance: "", rate: "", min_payment: "" }]);
  }

  function removeDebt(index: number) {
    setDebts(debts.filter((_, i) => i !== index));
  }

  function updateDebt(index: number, field: keyof DebtEntry, value: string) {
    const updated = [...debts];
    updated[index] = { ...updated[index], [field]: value };
    setDebts(updated);
  }

  function handleRun() {
    if (!selected) return;

    let params: Record<string, unknown> = {};

    switch (selected) {
      case "mortgage_payoff":
        params = {
          balance: parseFloat(mortgageBalance),
          interest_rate: parseFloat(mortgageRate),
          monthly_payment: parseFloat(mortgagePayment),
          extra_payment: parseFloat(mortgageExtra),
        };
        break;
      case "savings_projection":
        params = {
          current_amount: parseFloat(savingsCurrent),
          monthly_contribution: parseFloat(savingsMonthly),
          expected_return: parseFloat(savingsReturn),
          years: parseInt(savingsYears),
        };
        break;
      case "asset_change":
        params = {
          asset_value: parseFloat(assetValue),
          percent_change: parseFloat(assetChange),
        };
        break;
      case "debt_snowball":
        params = {
          debts: debts.map((d) => ({
            name: d.name,
            balance: parseFloat(d.balance),
            interest_rate: parseFloat(d.rate),
            min_payment: parseFloat(d.min_payment),
          })),
          extra_budget: parseFloat(extraBudget),
        };
        break;
    }

    runScenario.mutate(
      { type: selected, params },
      { onSuccess: (data) => setResult(data) }
    );
  }

  if (tier === "free") {
    return (
      <AppShell>
        <div className="max-w-2xl space-y-6">
          <div>
            <h2 className="text-2xl font-bold">Scenarios</h2>
            <p className="text-sm text-neutral-500">
              Model financial what-if scenarios to plan your future
            </p>
          </div>
          <UpgradePrompt feature="Financial Scenarios" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Scenarios</h2>
          <p className="text-sm text-neutral-500">
            Model financial what-if scenarios to plan your future
          </p>
        </div>

        {/* Scenario type selector */}
        {!selected && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {SCENARIO_CARDS.map((s) => (
              <Card
                key={s.type}
                className="cursor-pointer hover:border-indigo-300 hover:shadow-md transition-all"
                onClick={() => {
                  setSelected(s.type);
                  setResult(null);
                }}
              >
                <CardContent className="p-6 text-center">
                  <s.icon className="h-8 w-8 mx-auto text-indigo-600 mb-3" />
                  <h3 className="font-semibold text-sm">{s.title}</h3>
                  <p className="text-xs text-neutral-500 mt-1">{s.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Scenario form */}
        {selected && (
          <>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={() => { setSelected(null); setResult(null); }}>
                &larr; Back
              </Button>
              <Badge variant="outline" className="text-xs">
                {SCENARIO_CARDS.find((s) => s.type === selected)?.title}
              </Badge>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Calculator className="h-4 w-4" />
                  {SCENARIO_CARDS.find((s) => s.type === selected)?.title}
                </CardTitle>
                <CardDescription>Adjust parameters and run the projection</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Mortgage Payoff */}
                {selected === "mortgage_payoff" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Outstanding Balance</Label>
                      <Input
                        type="number"
                        value={mortgageBalance}
                        onChange={(e) => setMortgageBalance(e.target.value)}
                        placeholder="250000"
                      />
                    </div>
                    <div>
                      <Label>Interest Rate (%)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={mortgageRate}
                        onChange={(e) => setMortgageRate(e.target.value)}
                        placeholder="5.5"
                      />
                    </div>
                    <div>
                      <Label>Monthly Payment</Label>
                      <Input
                        type="number"
                        value={mortgagePayment}
                        onChange={(e) => setMortgagePayment(e.target.value)}
                        placeholder="1500"
                      />
                    </div>
                    <div>
                      <Label>Extra Monthly Payment</Label>
                      <Input
                        type="number"
                        value={mortgageExtra}
                        onChange={(e) => setMortgageExtra(e.target.value)}
                        placeholder="200"
                      />
                      <input
                        type="range"
                        min="0"
                        max="2000"
                        step="50"
                        value={mortgageExtra}
                        onChange={(e) => setMortgageExtra(e.target.value)}
                        className="w-full mt-2 accent-indigo-600"
                      />
                      <div className="flex justify-between text-xs text-neutral-400">
                        <span>{formatCurrency(0)}</span>
                        <span>{formatCurrency(parseFloat(mortgageExtra) || 0)}</span>
                        <span>{formatCurrency(2000)}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Savings Projection */}
                {selected === "savings_projection" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Current Savings</Label>
                      <Input
                        type="number"
                        value={savingsCurrent}
                        onChange={(e) => setSavingsCurrent(e.target.value)}
                        placeholder="10000"
                      />
                    </div>
                    <div>
                      <Label>Monthly Contribution</Label>
                      <Input
                        type="number"
                        value={savingsMonthly}
                        onChange={(e) => setSavingsMonthly(e.target.value)}
                        placeholder="500"
                      />
                    </div>
                    <div>
                      <Label>Expected Annual Return (%)</Label>
                      <Input
                        type="number"
                        step="0.1"
                        value={savingsReturn}
                        onChange={(e) => setSavingsReturn(e.target.value)}
                        placeholder="7"
                      />
                    </div>
                    <div>
                      <Label>Time Period (years)</Label>
                      <Input
                        type="number"
                        value={savingsYears}
                        onChange={(e) => setSavingsYears(e.target.value)}
                        placeholder="20"
                      />
                      <input
                        type="range"
                        min="1"
                        max="40"
                        step="1"
                        value={savingsYears}
                        onChange={(e) => setSavingsYears(e.target.value)}
                        className="w-full mt-2 accent-indigo-600"
                      />
                      <div className="flex justify-between text-xs text-neutral-400">
                        <span>1 yr</span>
                        <span>{savingsYears} yrs</span>
                        <span>40 yrs</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Asset Change */}
                {selected === "asset_change" && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>Asset Value</Label>
                      <Input
                        type="number"
                        value={assetValue}
                        onChange={(e) => setAssetValue(e.target.value)}
                        placeholder="500000"
                      />
                    </div>
                    <div>
                      <Label>Value Change (%)</Label>
                      <Input
                        type="number"
                        step="1"
                        value={assetChange}
                        onChange={(e) => setAssetChange(e.target.value)}
                        placeholder="10"
                      />
                      <input
                        type="range"
                        min="-50"
                        max="100"
                        step="1"
                        value={assetChange}
                        onChange={(e) => setAssetChange(e.target.value)}
                        className="w-full mt-2 accent-indigo-600"
                      />
                      <div className="flex justify-between text-xs text-neutral-400">
                        <span>-50%</span>
                        <span className={parseFloat(assetChange) >= 0 ? "text-emerald-600 font-medium" : "text-red-600 font-medium"}>
                          {parseFloat(assetChange) >= 0 ? "+" : ""}{assetChange}%
                        </span>
                        <span>+100%</span>
                      </div>
                    </div>
                    <div className="md:col-span-2">
                      <div className="flex gap-4 text-sm">
                        <div className="flex-1 rounded-lg bg-neutral-50 p-3">
                          <p className="text-neutral-500 text-xs">Current Value</p>
                          <p className="font-semibold">{formatCurrency(parseFloat(assetValue) || 0)}</p>
                        </div>
                        <div className="flex-1 rounded-lg bg-neutral-50 p-3">
                          <p className="text-neutral-500 text-xs">Projected Value</p>
                          <p className="font-semibold">
                            {formatCurrency((parseFloat(assetValue) || 0) * (1 + (parseFloat(assetChange) || 0) / 100))}
                          </p>
                        </div>
                        <div className="flex-1 rounded-lg bg-neutral-50 p-3">
                          <p className="text-neutral-500 text-xs">Difference</p>
                          <p className={`font-semibold ${parseFloat(assetChange) >= 0 ? "text-emerald-600" : "text-red-600"}`}>
                            {parseFloat(assetChange) >= 0 ? "+" : ""}
                            {formatCurrency((parseFloat(assetValue) || 0) * (parseFloat(assetChange) || 0) / 100)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Debt Snowball */}
                {selected === "debt_snowball" && (
                  <div className="space-y-4">
                    {debts.map((debt, i) => (
                      <div key={i} className="rounded-lg border border-neutral-200 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <Label className="text-sm font-medium">Debt {i + 1}</Label>
                          {debts.length > 1 && (
                            <button
                              onClick={() => removeDebt(i)}
                              className="text-neutral-400 hover:text-red-500"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div>
                            <Label className="text-xs">Name</Label>
                            <Input
                              value={debt.name}
                              onChange={(e) => updateDebt(i, "name", e.target.value)}
                              placeholder="Credit Card"
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Balance</Label>
                            <Input
                              type="number"
                              value={debt.balance}
                              onChange={(e) => updateDebt(i, "balance", e.target.value)}
                              placeholder="5000"
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Rate (%)</Label>
                            <Input
                              type="number"
                              step="0.1"
                              value={debt.rate}
                              onChange={(e) => updateDebt(i, "rate", e.target.value)}
                              placeholder="19.9"
                            />
                          </div>
                          <div>
                            <Label className="text-xs">Min Payment</Label>
                            <Input
                              type="number"
                              value={debt.min_payment}
                              onChange={(e) => updateDebt(i, "min_payment", e.target.value)}
                              placeholder="150"
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                    <Button variant="outline" size="sm" onClick={addDebt}>
                      <Plus className="h-4 w-4 mr-1" />
                      Add Debt
                    </Button>
                    <div>
                      <Label>Extra Monthly Budget</Label>
                      <Input
                        type="number"
                        value={extraBudget}
                        onChange={(e) => setExtraBudget(e.target.value)}
                        placeholder="200"
                      />
                      <input
                        type="range"
                        min="0"
                        max="2000"
                        step="50"
                        value={extraBudget}
                        onChange={(e) => setExtraBudget(e.target.value)}
                        className="w-full mt-2 accent-indigo-600"
                      />
                    </div>
                  </div>
                )}

                <Button
                  onClick={handleRun}
                  disabled={runScenario.isPending}
                  className="w-full bg-indigo-600 hover:bg-indigo-700"
                >
                  {runScenario.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Calculator className="h-4 w-4 mr-2" />
                      Run Scenario
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Results */}
            {result && (
              <>
                {/* Summary cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(result.summary).map(([key, value]) => (
                    <Card key={key}>
                      <CardContent className="p-4">
                        <p className="text-xs text-neutral-500 capitalize">
                          {key.replace(/_/g, " ")}
                        </p>
                        <p className="text-lg font-bold mt-1">
                          {typeof value === "number"
                            ? key.includes("month") || key.includes("year")
                              ? value
                              : formatCurrency(value)
                            : value}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Chart */}
                {result.data.length > 0 && (
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Projection</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-[350px]">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={result.data}>
                            <defs>
                              <linearGradient id="scenarioFill" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                              </linearGradient>
                            </defs>
                            <XAxis
                              dataKey="label"
                              tick={{ fontSize: 11 }}
                              tickLine={false}
                              axisLine={false}
                            />
                            <YAxis
                              tick={{ fontSize: 11 }}
                              tickLine={false}
                              axisLine={false}
                              tickFormatter={(v) => formatCurrency(v)}
                            />
                            <Tooltip
                              formatter={(value) => formatCurrency(Number(value))}
                              contentStyle={{ fontSize: 12 }}
                            />
                            <Area
                              type="monotone"
                              dataKey="value"
                              stroke="#6366f1"
                              fill="url(#scenarioFill)"
                              strokeWidth={2}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}
