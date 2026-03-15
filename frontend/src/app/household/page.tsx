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
import {
  useHousehold,
  useCreateHousehold,
  useInviteMember,
  useCombinedWealth,
  useHouseholdGoals,
  useCreateHouseholdGoal,
} from "@/hooks/use-household";
import { formatCurrency } from "@/lib/utils";
import {
  Users,
  UserPlus,
  Mail,
  Loader2,
  Target,
  Plus,
  DollarSign,
} from "lucide-react";

export default function HouseholdPage() {
  const { data: subscription } = useSubscription();
  const tier = subscription?.tier || "free";
  const { data: household, isLoading } = useHousehold();
  const { data: combinedWealth } = useCombinedWealth();
  const { data: goals } = useHouseholdGoals();
  const createHousehold = useCreateHousehold();
  const inviteMember = useInviteMember();
  const createGoal = useCreateHouseholdGoal();

  const [householdName, setHouseholdName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [goalName, setGoalName] = useState("");
  const [goalAmount, setGoalAmount] = useState("");
  const [showGoalForm, setShowGoalForm] = useState(false);

  if (tier !== "family") {
    return (
      <AppShell>
        <div className="max-w-2xl space-y-6">
          <div>
            <h2 className="text-2xl font-bold">Household</h2>
            <p className="text-sm text-neutral-500">
              Combine finances with your partner or family
            </p>
          </div>
          <UpgradePrompt feature="Household Finance" tier="family" />
        </div>
      </AppShell>
    );
  }

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center gap-2 text-neutral-500">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading...
        </div>
      </AppShell>
    );
  }

  // No household yet - show creation
  if (!household) {
    return (
      <AppShell>
        <div className="max-w-md mx-auto space-y-6 pt-12">
          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
              <Users className="h-8 w-8 text-purple-600" />
            </div>
            <h2 className="text-2xl font-bold">Create Your Household</h2>
            <p className="text-sm text-neutral-500 mt-1">
              Combine finances with your partner or family members
            </p>
          </div>
          <Card>
            <CardContent className="p-6 space-y-4">
              <div>
                <Label>Household Name</Label>
                <Input
                  value={householdName}
                  onChange={(e) => setHouseholdName(e.target.value)}
                  placeholder="e.g. The Smith Family"
                />
              </div>
              <Button
                className="w-full bg-indigo-600 hover:bg-indigo-700"
                onClick={() => createHousehold.mutate({ name: householdName })}
                disabled={!householdName || createHousehold.isPending}
              >
                {createHousehold.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Users className="h-4 w-4 mr-2" />
                    Create Household
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">{household.name}</h2>
          <p className="text-sm text-neutral-500">
            Manage your household members and shared finances
          </p>
        </div>

        {/* Combined Net Worth */}
        {combinedWealth && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Combined Net Worth
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-indigo-600">
                {formatCurrency(combinedWealth.net_worth, combinedWealth.currency)}
              </p>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="rounded-lg bg-emerald-50 p-3">
                  <p className="text-xs text-emerald-600">Total Assets</p>
                  <p className="text-lg font-semibold text-emerald-700">
                    {formatCurrency(combinedWealth.total_assets, combinedWealth.currency)}
                  </p>
                </div>
                <div className="rounded-lg bg-red-50 p-3">
                  <p className="text-xs text-red-600">Total Liabilities</p>
                  <p className="text-lg font-semibold text-red-700">
                    {formatCurrency(combinedWealth.total_liabilities, combinedWealth.currency)}
                  </p>
                </div>
              </div>
              {combinedWealth.members.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-xs text-neutral-500 font-medium uppercase tracking-wider">By Member</p>
                  {combinedWealth.members.map((m) => (
                    <div key={m.name} className="flex items-center justify-between text-sm">
                      <span className="text-neutral-700">{m.name}</span>
                      <span className="font-medium">{formatCurrency(m.net_worth, combinedWealth.currency)}</span>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Members */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="h-4 w-4" />
              Members
            </CardTitle>
            <CardDescription>People in your household</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              {household.members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between rounded-lg border border-neutral-200 px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-sm font-medium text-indigo-700">
                        {(member.name || member.email).charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium">{member.name || member.email}</p>
                      <p className="text-xs text-neutral-500">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      variant={member.status === "accepted" ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {member.status === "accepted" ? "Active" : "Pending"}
                    </Badge>
                    <Badge variant="outline" className="text-xs capitalize">
                      {member.role}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>

            {/* Invite form */}
            <div className="border-t pt-4">
              <Label className="text-sm font-medium">Invite a member</Label>
              <div className="flex gap-2 mt-2">
                <Input
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="partner@email.com"
                  type="email"
                  className="flex-1"
                />
                <Button
                  onClick={() => {
                    inviteMember.mutate(
                      { email: inviteEmail },
                      { onSuccess: () => setInviteEmail("") }
                    );
                  }}
                  disabled={!inviteEmail || inviteMember.isPending}
                >
                  {inviteMember.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <>
                      <UserPlus className="h-4 w-4 mr-1" />
                      Invite
                    </>
                  )}
                </Button>
              </div>
              {inviteMember.isSuccess && (
                <div className="flex items-center gap-1.5 text-xs text-emerald-600 mt-2">
                  <Mail className="h-3 w-3" />
                  Invitation sent
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Shared Goals */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="h-4 w-4" />
                Shared Goals
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowGoalForm(!showGoalForm)}
              >
                <Plus className="h-4 w-4 mr-1" />
                New Goal
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {showGoalForm && (
              <div className="rounded-lg border border-neutral-200 p-4 space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs">Goal Name</Label>
                    <Input
                      value={goalName}
                      onChange={(e) => setGoalName(e.target.value)}
                      placeholder="Family holiday fund"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Target Amount</Label>
                    <Input
                      type="number"
                      value={goalAmount}
                      onChange={(e) => setGoalAmount(e.target.value)}
                      placeholder="10000"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => {
                      createGoal.mutate(
                        { name: goalName, target_amount: parseFloat(goalAmount) },
                        {
                          onSuccess: () => {
                            setGoalName("");
                            setGoalAmount("");
                            setShowGoalForm(false);
                          },
                        }
                      );
                    }}
                    disabled={!goalName || !goalAmount || createGoal.isPending}
                  >
                    Create
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setShowGoalForm(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}

            {goals && goals.length > 0 ? (
              <div className="space-y-3">
                {goals.map((goal) => (
                  <div key={goal.id} className="rounded-lg border border-neutral-200 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-sm font-medium">{goal.name}</h4>
                      <span className="text-xs text-neutral-500">
                        {Math.round(goal.progress_pct)}%
                      </span>
                    </div>
                    <div className="w-full bg-neutral-100 rounded-full h-2">
                      <div
                        className="bg-indigo-600 h-2 rounded-full transition-all"
                        style={{ width: `${Math.min(100, goal.progress_pct)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-neutral-500 mt-1.5">
                      <span>{formatCurrency(goal.current_value, goal.currency)}</span>
                      <span>{formatCurrency(goal.target_amount, goal.currency)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              !showGoalForm && (
                <p className="text-sm text-neutral-500 text-center py-4">
                  No shared goals yet. Create one to track progress together.
                </p>
              )
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
