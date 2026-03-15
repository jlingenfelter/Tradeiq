"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AddPositionForm } from "@/components/portfolio/AddPositionForm";
import { CsvUploadWizard } from "@/components/portfolio/CsvUploadWizard";
import type { Portfolio } from "@/types";

type Step = "name" | "method" | "manual" | "csv" | "trading212";

interface T212SyncResult {
  imported: number;
  skipped: number;
  errors: string[];
}

interface T212TestResult {
  success: boolean;
  account_id: string | null;
  currency: string | null;
  message: string;
}

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>("name");
  const [portfolioName, setPortfolioName] = useState("My Portfolio");
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(false);
  const [t212Key, setT212Key] = useState("");
  const [t212Env, setT212Env] = useState("live");
  const [t212Status, setT212Status] = useState("");
  const [t212Result, setT212Result] = useState<T212SyncResult | null>(null);
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    router.replace("/login");
    return null;
  }

  async function handleCreatePortfolio(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const p = await api.post<Portfolio>("/portfolios", { name: portfolioName });
      setPortfolio(p);
      setStep("method");
    } finally {
      setLoading(false);
    }
  }

  function handleDone() {
    router.push("/overview");
  }

  async function handleT212Test() {
    setT212Status("Testing connection...");
    try {
      const res = await api.post<T212TestResult>("/trading212/test", {
        api_key: t212Key,
        environment: t212Env,
      });
      if (res.success) {
        setT212Status(`Connected! Account: ${res.currency} account`);
      } else {
        setT212Status(`Error: ${res.message}`);
      }
    } catch (err: unknown) {
      setT212Status(err instanceof Error ? err.message : "Connection failed");
    }
  }

  async function handleT212Sync() {
    if (!portfolio) return;
    setLoading(true);
    setT212Status("Importing positions...");
    try {
      const result = await api.post<T212SyncResult>("/trading212/sync", {
        api_key: t212Key,
        portfolio_id: portfolio.id,
        environment: t212Env,
      });
      setT212Result(result);
      setT212Status(`Imported ${result.imported} positions`);
    } catch (err: unknown) {
      setT212Status(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4 py-12">
      <div className="w-full max-w-lg space-y-6">
        {step === "name" && (
          <Card>
            <CardHeader>
              <CardTitle>Create Your Portfolio</CardTitle>
              <CardDescription>Give your portfolio a name to get started</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreatePortfolio} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Portfolio Name</Label>
                  <Input id="name" value={portfolioName} onChange={(e) => setPortfolioName(e.target.value)} required />
                </div>
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Creating..." : "Continue"}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {step === "method" && (
          <Card>
            <CardHeader>
              <CardTitle>Add Your Holdings</CardTitle>
              <CardDescription>Choose how you want to add your positions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("trading212")}>
                <div className="text-left">
                  <div className="font-medium">Connect Trading 212</div>
                  <div className="text-sm text-neutral-500">Auto-import positions via API key</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("csv")}>
                <div className="text-left">
                  <div className="font-medium">Upload CSV</div>
                  <div className="text-sm text-neutral-500">Import from Trading 212 or spreadsheet export</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("manual")}>
                <div className="text-left">
                  <div className="font-medium">Add Manually</div>
                  <div className="text-sm text-neutral-500">Enter positions one at a time</div>
                </div>
              </Button>
              <Button variant="ghost" className="w-full" onClick={handleDone}>
                Skip for now
              </Button>
            </CardContent>
          </Card>
        )}

        {step === "trading212" && portfolio && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connect Trading 212</CardTitle>
                <CardDescription>
                  Enter your API key from Trading 212 Settings → API (Beta)
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="t212key">API Key</Label>
                  <Input
                    id="t212key"
                    type="password"
                    value={t212Key}
                    onChange={(e) => setT212Key(e.target.value)}
                    placeholder="Paste your Trading 212 API key"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="t212env">Environment</Label>
                  <select
                    id="t212env"
                    className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                    value={t212Env}
                    onChange={(e) => setT212Env(e.target.value)}
                  >
                    <option value="live">Live (Real Money)</option>
                    <option value="demo">Demo (Paper Trading)</option>
                  </select>
                </div>

                {t212Status && (
                  <div className={`rounded-md p-3 text-sm ${
                    t212Status.startsWith("Error") || t212Status.includes("failed")
                      ? "bg-red-50 text-red-700"
                      : t212Status.startsWith("Connected") || t212Status.startsWith("Imported")
                      ? "bg-green-50 text-green-700"
                      : "bg-blue-50 text-blue-700"
                  }`}>
                    {t212Status}
                  </div>
                )}

                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={handleT212Test} disabled={!t212Key || loading}>
                    Test Connection
                  </Button>
                  <Button className="flex-1" onClick={handleT212Sync} disabled={!t212Key || loading}>
                    {loading ? "Importing..." : "Import Positions"}
                  </Button>
                </div>

                {t212Result && t212Result.imported > 0 && (
                  <div className="space-y-3 pt-2">
                    <div className="text-sm text-neutral-500">
                      {t212Result.imported} positions imported
                      {t212Result.skipped > 0 && `, ${t212Result.skipped} skipped`}
                    </div>
                    {t212Result.errors.length > 0 && (
                      <div className="text-xs text-red-600">
                        {t212Result.errors.map((e, i) => <div key={i}>{e}</div>)}
                      </div>
                    )}
                    <Button onClick={handleDone} className="w-full">
                      Go to Dashboard
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
            <Button variant="ghost" className="w-full" onClick={() => setStep("method")}>
              Back
            </Button>
          </div>
        )}

        {step === "manual" && portfolio && (
          <div className="space-y-4">
            <AddPositionForm portfolioId={portfolio.id} onDone={handleDone} />
            <Button variant="ghost" className="w-full" onClick={() => setStep("method")}>
              Back
            </Button>
          </div>
        )}

        {step === "csv" && portfolio && (
          <div className="space-y-4">
            <CsvUploadWizard portfolioId={portfolio.id} onDone={handleDone} />
            <Button variant="ghost" className="w-full" onClick={() => setStep("method")}>
              Back
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
