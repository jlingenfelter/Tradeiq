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
import { Trash2 } from "lucide-react";

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
