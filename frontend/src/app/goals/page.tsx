"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { useGoals, useCreateGoal, useDeleteGoal } from "@/hooks/use-goals";
import { formatCurrency } from "@/lib/utils";
import { Plus, Trash2, TrendingUp, Calendar, Target } from "lucide-react";
import type { WealthGoal } from "@/types";

const GOAL_TYPES = [
  { value: "net_worth", label: "Net Worth" },
  { value: "savings", label: "Cash Savings" },
  { value: "investment", label: "Investment Value" },
  { value: "emergency_fund", label: "Emergency Fund" },
  { value: "debt_payoff", label: "Debt Payoff" },
];

const EMOJIS = ["🎯", "🏠", "🚗", "✈️", "💰", "🎓", "👶", "🏖️", "💎", "🔥", "⭐", "🚀"];

function GoalProgressRing({ pct, size = 120 }: { pct: number; size?: number }) {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;
  const color = pct >= 100 ? "#22c55e" : pct >= 50 ? "#6366f1" : pct >= 25 ? "#f59e0b" : "#94a3b8";

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#e2e8f0"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-700 ease-out"
      />
    </svg>
  );
}

function GoalCard({ goal }: { goal: WealthGoal }) {
  const deleteGoal = useDeleteGoal();
  const isComplete = goal.progress_pct >= 100;

  return (
    <Card className={isComplete ? "border-green-200 bg-green-50/30" : ""}>
      <CardContent className="p-6">
        <div className="flex items-start gap-5">
          {/* Progress ring */}
          <div className="relative flex-shrink-0">
            <GoalProgressRing pct={goal.progress_pct} />
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl">{goal.emoji}</span>
              <span className="text-xs font-bold mt-0.5">
                {Math.round(goal.progress_pct)}%
              </span>
            </div>
          </div>

          {/* Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-lg truncate">{goal.name}</h3>
              <button
                onClick={() => deleteGoal.mutate(goal.id)}
                className="text-neutral-400 hover:text-red-500 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>

            <p className="text-sm text-neutral-500 mt-1">
              {formatCurrency(goal.current_value, goal.currency)} of{" "}
              {formatCurrency(goal.target_amount, goal.currency)}
            </p>

            {/* Milestone dots */}
            <div className="flex gap-1.5 mt-3">
              {goal.milestones.map((m) => (
                <div
                  key={m.pct}
                  className={`h-2.5 w-2.5 rounded-full transition-all ${
                    m.reached
                      ? "bg-indigo-500 scale-110"
                      : "bg-neutral-200"
                  }`}
                  title={`${m.pct}%`}
                />
              ))}
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap gap-3 mt-3">
              {goal.monthly_growth !== 0 && (
                <div className="flex items-center gap-1 text-xs text-neutral-500">
                  <TrendingUp className="h-3 w-3" />
                  <span>
                    {goal.monthly_growth > 0 ? "+" : ""}
                    {formatCurrency(goal.monthly_growth, goal.currency)}/mo
                  </span>
                </div>
              )}
              {goal.days_remaining !== null && (
                <div className="flex items-center gap-1 text-xs text-neutral-500">
                  <Calendar className="h-3 w-3" />
                  <span>{goal.days_remaining} days left</span>
                </div>
              )}
              {goal.on_track !== null && (
                <Badge variant={goal.on_track ? "default" : "destructive"} className="text-xs">
                  {goal.on_track ? "On track" : "Behind pace"}
                </Badge>
              )}
              {goal.projected_date && !goal.target_date && (
                <div className="flex items-center gap-1 text-xs text-neutral-500">
                  <Target className="h-3 w-3" />
                  <span>
                    Est. {new Date(goal.projected_date).toLocaleDateString("en-GB", { month: "short", year: "numeric" })}
                  </span>
                </div>
              )}
            </div>

            {/* Remaining */}
            <p className="text-xs text-neutral-400 mt-2">
              {formatCurrency(goal.remaining, goal.currency)} {goal.amount_label}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function GoalsPage() {
  const { data: goals, isLoading } = useGoals();
  const createGoal = useCreateGoal();
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [goalType, setGoalType] = useState("net_worth");
  const [emoji, setEmoji] = useState("🎯");

  const handleCreate = () => {
    if (!name || !amount) return;
    createGoal.mutate(
      {
        name,
        target_amount: parseFloat(amount),
        target_date: targetDate || undefined,
        goal_type: goalType,
        emoji,
      },
      {
        onSuccess: () => {
          setShowForm(false);
          setName("");
          setAmount("");
          setTargetDate("");
          setGoalType("net_worth");
          setEmoji("🎯");
        },
      }
    );
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Goals</h2>
            <p className="text-sm text-neutral-500">
              Set targets and track your progress
            </p>
          </div>
          <Button onClick={() => setShowForm(!showForm)} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            New Goal
          </Button>
        </div>

        {/* Create form */}
        {showForm && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Create a goal</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Goal name</Label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. First £100k, House deposit"
                  />
                </div>
                <div>
                  <Label>Target amount</Label>
                  <Input
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="100000"
                  />
                </div>
                <div>
                  <Label>Target date (optional)</Label>
                  <Input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Goal type</Label>
                  <select
                    value={goalType}
                    onChange={(e) => setGoalType(e.target.value)}
                    className="w-full rounded-md border px-3 py-2 text-sm"
                  >
                    {GOAL_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <Label>Icon</Label>
                <div className="flex gap-2 mt-1">
                  {EMOJIS.map((e) => (
                    <button
                      key={e}
                      onClick={() => setEmoji(e)}
                      className={`text-xl p-1.5 rounded-md transition-colors ${
                        emoji === e ? "bg-indigo-100 ring-2 ring-indigo-500" : "hover:bg-neutral-100"
                      }`}
                    >
                      {e}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleCreate} disabled={!name || !amount}>
                  Create Goal
                </Button>
                <Button variant="outline" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Loading */}
        {isLoading && (
          <p className="text-neutral-500">Loading goals...</p>
        )}

        {/* Goals list */}
        {goals && goals.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {goals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {goals && goals.length === 0 && !showForm && (
          <EmptyState
            icon={Target}
            title="Set your first goal"
            description="Track your progress towards financial milestones"
            action={{ label: "Create your first goal", onClick: () => setShowForm(true) }}
          />
        )}
      </div>
    </AppShell>
  );
}
