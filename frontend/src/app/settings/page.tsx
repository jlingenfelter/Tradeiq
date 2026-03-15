"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Trash2, Crown, Key, Copy, Check, Plus, Loader2 } from "lucide-react";
import { useSubscription, useCreatePortal } from "@/hooks/use-subscription";
import { useApiKeys, useCreateApiKey, useDeleteApiKey } from "@/hooks/use-api-keys";
import type { ApiKeyCreated } from "@/hooks/use-api-keys";
import { UpgradePrompt } from "@/components/subscription/UpgradePrompt";

const CURRENCIES = ["USD", "GBP", "EUR", "CHF", "CAD", "AUD", "JPY", "SGD", "HKD"];
const TIMEZONES = [
  "UTC", "America/New_York", "America/Chicago", "America/Los_Angeles",
  "Europe/London", "Europe/Paris", "Europe/Zurich",
  "Asia/Singapore", "Asia/Hong_Kong", "Asia/Tokyo",
  "Australia/Sydney",
];

export default function SettingsPage() {
  const { user, logout } = useAuth();
  const [baseCurrency, setBaseCurrency] = useState(user?.base_currency || "USD");
  const [timezone, setTimezone] = useState(user?.timezone || "UTC");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function handleSavePreferences() {
    setSaving(true);
    try {
      await api.patch("/auth/me", { base_currency: baseCurrency, timezone });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {}
    setSaving(false);
  }

  return (
    <AppShell>
      <div className="max-w-2xl space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Settings</h2>
          <p className="text-sm text-neutral-500">Manage your account and preferences</p>
        </div>

        {/* Account */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label className="text-neutral-500">Email</Label>
              <div className="text-sm font-medium">{user?.email}</div>
            </div>
            <div>
              <Label className="text-neutral-500">Member since</Label>
              <div className="text-sm font-medium">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : "—"}
              </div>
            </div>
            <Button variant="outline" onClick={logout} className="mt-2">
              Sign out
            </Button>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Preferences</CardTitle>
            <CardDescription>Configure your display settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Base Currency</Label>
              <select
                className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm mt-1"
                value={baseCurrency}
                onChange={(e) => setBaseCurrency(e.target.value)}
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <p className="text-xs text-neutral-400 mt-1">
                All values will be displayed in this currency
              </p>
            </div>
            <div>
              <Label>Timezone</Label>
              <select
                className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm mt-1"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>{tz}</option>
                ))}
              </select>
            </div>
            <Button onClick={handleSavePreferences} disabled={saving}>
              {saving ? "Saving..." : saved ? "Saved" : "Save Preferences"}
            </Button>
          </CardContent>
        </Card>

        {/* Subscription & Billing */}
        <BillingCard />

        {/* API Keys */}
        <ApiKeysCard />

        {/* Data Management */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Data</CardTitle>
            <CardDescription>Manage your wealth data</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-neutral-500">
              Your data is stored securely and is only accessible by you.
            </p>
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <Card>
          <CardContent className="p-4">
            <p className="text-xs text-neutral-400 leading-relaxed">
              Wealth Copilot is a read-only wealth monitoring and analysis tool. It does not
              execute trades, manage portfolios, move money, or provide personalized investment advice.
              All analytics are for informational purposes only. Asset valuations may be based on
              manual entries or estimates. Past performance does not guarantee future results.
              Always consult a qualified financial advisor before making investment decisions.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}

function BillingCard() {
  const { data: subscription } = useSubscription();
  const portal = useCreatePortal();
  const tier = subscription?.tier || "free";
  const periodEnd = subscription?.current_period_end;

  const TIER_DISPLAY: Record<string, { label: string; color: string }> = {
    free: { label: "Free", color: "bg-slate-100 text-slate-700" },
    pro: { label: "Pro", color: "bg-indigo-100 text-indigo-700" },
    family: { label: "Family", color: "bg-purple-100 text-purple-700" },
  };

  const display = TIER_DISPLAY[tier] || TIER_DISPLAY.free;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Crown className="h-4 w-4" />
          Subscription & Billing
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <div>
            <Label className="text-neutral-500">Current Plan</Label>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={display.color}>{display.label}</Badge>
              {subscription?.cancel_at_period_end && (
                <span className="text-xs text-amber-600">Cancels at period end</span>
              )}
            </div>
          </div>
        </div>

        {periodEnd && (
          <div>
            <Label className="text-neutral-500">
              {subscription?.cancel_at_period_end ? "Access until" : "Next billing date"}
            </Label>
            <div className="text-sm font-medium">
              {new Date(periodEnd).toLocaleDateString("en-GB", {
                day: "numeric", month: "long", year: "numeric",
              })}
            </div>
          </div>
        )}

        <div className="flex gap-2">
          {tier === "free" ? (
            <Button asChild>
              <a href="/pricing">Upgrade Plan</a>
            </Button>
          ) : (
            <Button
              variant="outline"
              onClick={() => portal.mutate()}
              disabled={portal.isPending}
            >
              {portal.isPending ? "Loading..." : "Manage Billing"}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ApiKeysCard() {
  const { data: subscription } = useSubscription();
  const tier = subscription?.tier || "free";
  const { data: keys, isLoading } = useApiKeys();
  const createKey = useCreateApiKey();
  const deleteKey = useDeleteApiKey();

  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreated | null>(null);
  const [copied, setCopied] = useState(false);

  function handleCreate() {
    if (!newKeyName) return;
    createKey.mutate(
      { name: newKeyName },
      {
        onSuccess: (data) => {
          setCreatedKey(data);
          setNewKeyName("");
        },
      }
    );
  }

  function handleCopy(text: string) {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (tier === "free") {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Keys
          </CardTitle>
        </CardHeader>
        <CardContent>
          <UpgradePrompt feature="API Access" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Key className="h-4 w-4" />
          API Keys
        </CardTitle>
        <CardDescription>Manage programmatic access to your data</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Created key banner */}
        {createdKey && (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 space-y-2">
            <p className="text-sm font-medium text-emerald-800">
              API key created. Copy it now - it will not be shown again.
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 rounded bg-white px-3 py-2 text-sm font-mono border border-emerald-200 select-all">
                {createdKey.key}
              </code>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleCopy(createdKey.key)}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-emerald-600" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            <Button
              size="sm"
              variant="ghost"
              className="text-xs"
              onClick={() => setCreatedKey(null)}
            >
              Dismiss
            </Button>
          </div>
        )}

        {/* Create form */}
        <div className="flex gap-2">
          <Input
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key name, e.g. My App"
            className="flex-1"
          />
          <Button
            onClick={handleCreate}
            disabled={!newKeyName || createKey.isPending}
          >
            {createKey.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Plus className="h-4 w-4 mr-1" />
                Create Key
              </>
            )}
          </Button>
        </div>

        {/* Key list */}
        {isLoading && <p className="text-sm text-neutral-500">Loading keys...</p>}

        {keys && keys.length > 0 && (
          <div className="space-y-2">
            {keys.map((k) => (
              <div
                key={k.id}
                className="flex items-center justify-between rounded-lg border border-neutral-200 px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium">{k.name}</p>
                  <div className="flex items-center gap-3 text-xs text-neutral-500 mt-0.5">
                    <span className="font-mono">{k.prefix}...</span>
                    <span>
                      {k.last_used_at
                        ? `Last used ${new Date(k.last_used_at).toLocaleDateString()}`
                        : "Never used"}
                    </span>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => deleteKey.mutate(k.id)}
                  disabled={deleteKey.isPending}
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {keys && keys.length === 0 && !createdKey && (
          <p className="text-sm text-neutral-500 text-center py-2">
            No API keys yet. Create one to get started.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
