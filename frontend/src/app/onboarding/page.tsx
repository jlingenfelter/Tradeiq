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

type Step = "name" | "method" | "manual" | "csv" | "trading212" | "alpaca" | "ibkr" | "ig" | "tradier" | "crypto";

interface SyncResult {
  imported: number;
  skipped: number;
  errors: string[];
  chain?: string;
}

interface TestResult {
  success: boolean;
  message: string;
  [key: string]: unknown;
}

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>("name");
  const [portfolioName, setPortfolioName] = useState("My Portfolio");
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  // Broker-specific fields
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [env, setEnv] = useState("live");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [gatewayUrl, setGatewayUrl] = useState("https://localhost:5000");
  const [accountId, setAccountId] = useState("");
  const [walletAddress, setWalletAddress] = useState("");
  // IG tokens after auth
  const [igToken, setIgToken] = useState("");
  const [igCst, setIgCst] = useState("");

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
    router.push("/dashboard");
  }

  function resetBrokerState() {
    setApiKey("");
    setApiSecret("");
    setEnv("live");
    setUsername("");
    setPassword("");
    setGatewayUrl("https://localhost:5000");
    setAccountId("");
    setWalletAddress("");
    setIgToken("");
    setIgCst("");
    setStatus("");
    setSyncResult(null);
  }

  function goBack() {
    resetBrokerState();
    setStep("method");
  }

  // --- Generic test/sync helpers ---
  async function handleTest(endpoint: string, body: Record<string, unknown>) {
    setStatus("Testing connection...");
    try {
      const res = await api.post<TestResult>(endpoint, body);
      if (res.success) {
        setStatus(res.message || "Connected successfully");
        // For IG, save tokens
        if ("access_token" in res && res.access_token) {
          setIgToken(res.access_token as string);
          setIgCst((res.cst as string) || "");
          if (res.account_id) setAccountId(res.account_id as string);
        }
        // For IBKR, save accounts
        if ("accounts" in res && Array.isArray(res.accounts) && res.accounts.length > 0) {
          setAccountId(res.accounts[0]);
        }
        // For Tradier, save account_id
        if ("account_id" in res && res.account_id && typeof res.account_id === "string") {
          setAccountId(res.account_id);
        }
      } else {
        setStatus(`Error: ${res.message}`);
      }
    } catch (err: unknown) {
      setStatus(err instanceof Error ? err.message : "Connection failed");
    }
  }

  async function handleSync(endpoint: string, body: Record<string, unknown>) {
    if (!portfolio) return;
    setLoading(true);
    setStatus("Importing positions...");
    try {
      const result = await api.post<SyncResult>(endpoint, { ...body, portfolio_id: portfolio.id });
      setSyncResult(result);
      const extra = result.chain ? ` from ${result.chain}` : "";
      setStatus(`Imported ${result.imported} positions${extra}`);
    } catch (err: unknown) {
      setStatus(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setLoading(false);
    }
  }

  function renderStatus() {
    if (!status) return null;
    const isError = status.startsWith("Error") || status.includes("failed") || status.includes("Invalid");
    const isSuccess = status.startsWith("Connected") || status.startsWith("Imported") || status.startsWith("Found") || status.startsWith("Authenticated");
    return (
      <div className={`rounded-md p-3 text-sm ${
        isError ? "bg-red-50 text-red-700"
          : isSuccess ? "bg-green-50 text-green-700"
          : "bg-blue-50 text-blue-700"
      }`}>
        {status}
      </div>
    );
  }

  function renderSyncResult() {
    if (!syncResult || syncResult.imported === 0) return null;
    return (
      <div className="space-y-3 pt-2">
        <div className="text-sm text-neutral-500">
          {syncResult.imported} positions imported
          {syncResult.skipped > 0 && `, ${syncResult.skipped} skipped`}
        </div>
        {syncResult.errors.length > 0 && (
          <div className="text-xs text-red-600">
            {syncResult.errors.map((e, i) => <div key={i}>{e}</div>)}
          </div>
        )}
        <Button onClick={handleDone} className="w-full">
          Go to Dashboard
        </Button>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-indigo-50/50 px-4 py-12">
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
              <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider pt-1">Broker Integrations</p>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("trading212")}>
                <div className="text-left">
                  <div className="font-medium">Trading 212</div>
                  <div className="text-sm text-neutral-500">Auto-import via API key</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("alpaca")}>
                <div className="text-left">
                  <div className="font-medium">Alpaca</div>
                  <div className="text-sm text-neutral-500">Connect with API key and secret</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("ibkr")}>
                <div className="text-left">
                  <div className="font-medium">Interactive Brokers</div>
                  <div className="text-sm text-neutral-500">Connect via IB Gateway (Client Portal API)</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("ig")}>
                <div className="text-left">
                  <div className="font-medium">IG Group</div>
                  <div className="text-sm text-neutral-500">Connect with API key and credentials</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("tradier")}>
                <div className="text-left">
                  <div className="font-medium">Tradier</div>
                  <div className="text-sm text-neutral-500">Connect with OAuth access token</div>
                </div>
              </Button>

              <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider pt-3">Crypto</p>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("crypto")}>
                <div className="text-left">
                  <div className="font-medium">Crypto Wallet</div>
                  <div className="text-sm text-neutral-500">Read ETH or BTC wallet balances on-chain</div>
                </div>
              </Button>

              <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider pt-3">Manual</p>
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

        {/* Trading 212 */}
        {step === "trading212" && portfolio && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connect Trading 212</CardTitle>
                <CardDescription>Enter your API key from Trading 212 Settings &rarr; API (Beta)</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Paste your Trading 212 API key" />
                </div>
                <div className="space-y-2">
                  <Label>Environment</Label>
                  <select className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                    <option value="live">Live (Real Money)</option>
                    <option value="demo">Demo (Paper Trading)</option>
                  </select>
                </div>
                {renderStatus()}
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => handleTest("/trading212/test", { api_key: apiKey, environment: env })} disabled={!apiKey || loading}>
                    Test Connection
                  </Button>
                  <Button className="flex-1" onClick={() => handleSync("/trading212/sync", { api_key: apiKey, environment: env })} disabled={!apiKey || loading}>
                    {loading ? "Importing..." : "Import Positions"}
                  </Button>
                </div>
                {renderSyncResult()}
              </CardContent>
            </Card>
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}

        {/* Alpaca */}
        {step === "alpaca" && portfolio && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connect Alpaca</CardTitle>
                <CardDescription>Enter your API key and secret from the Alpaca dashboard</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="APCA API Key ID" />
                </div>
                <div className="space-y-2">
                  <Label>API Secret</Label>
                  <Input type="password" value={apiSecret} onChange={(e) => setApiSecret(e.target.value)} placeholder="APCA API Secret Key" />
                </div>
                <div className="space-y-2">
                  <Label>Environment</Label>
                  <select className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                    <option value="live">Live</option>
                    <option value="paper">Paper Trading</option>
                  </select>
                </div>
                {renderStatus()}
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => handleTest("/alpaca/test", { api_key: apiKey, api_secret: apiSecret, environment: env })} disabled={!apiKey || !apiSecret || loading}>
                    Test Connection
                  </Button>
                  <Button className="flex-1" onClick={() => handleSync("/alpaca/sync", { api_key: apiKey, api_secret: apiSecret, environment: env })} disabled={!apiKey || !apiSecret || loading}>
                    {loading ? "Importing..." : "Import Positions"}
                  </Button>
                </div>
                {renderSyncResult()}
              </CardContent>
            </Card>
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}

        {/* Interactive Brokers */}
        {step === "ibkr" && portfolio && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connect Interactive Brokers</CardTitle>
                <CardDescription>
                  Requires IB Gateway or Client Portal API running locally. Download from IBKR website.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Gateway URL</Label>
                  <Input value={gatewayUrl} onChange={(e) => setGatewayUrl(e.target.value)} placeholder="https://localhost:5000" />
                </div>
                {accountId && (
                  <div className="space-y-2">
                    <Label>Account ID</Label>
                    <Input value={accountId} onChange={(e) => setAccountId(e.target.value)} />
                  </div>
                )}
                {renderStatus()}
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => handleTest("/ibkr/test", { gateway_url: gatewayUrl })} disabled={loading}>
                    Test Connection
                  </Button>
                  <Button className="flex-1" onClick={() => handleSync("/ibkr/sync", { gateway_url: gatewayUrl, ibkr_account_id: accountId })} disabled={!accountId || loading}>
                    {loading ? "Importing..." : "Import Positions"}
                  </Button>
                </div>
                {renderSyncResult()}
              </CardContent>
            </Card>
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}

        {/* IG Group */}
        {step === "ig" && portfolio && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connect IG Group</CardTitle>
                <CardDescription>Enter your IG API key and login credentials</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <Input value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Your IG API key" />
                </div>
                <div className="space-y-2">
                  <Label>Username</Label>
                  <Input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="IG username" />
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="IG password" />
                </div>
                <div className="space-y-2">
                  <Label>Environment</Label>
                  <select className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                    <option value="live">Live</option>
                    <option value="demo">Demo</option>
                  </select>
                </div>
                {renderStatus()}
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => handleTest("/ig/test", { api_key: apiKey, username, password, environment: env })} disabled={!apiKey || !username || !password || loading}>
                    Authenticate
                  </Button>
                  <Button className="flex-1" onClick={() => handleSync("/ig/sync", { api_key: apiKey, access_token: igToken, cst: igCst, environment: env })} disabled={!igToken || loading}>
                    {loading ? "Importing..." : "Import Positions"}
                  </Button>
                </div>
                {renderSyncResult()}
              </CardContent>
            </Card>
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}

        {/* Tradier */}
        {step === "tradier" && portfolio && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connect Tradier</CardTitle>
                <CardDescription>Enter your Tradier OAuth access token from your API management page</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Access Token</Label>
                  <Input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Tradier access token" />
                </div>
                <div className="space-y-2">
                  <Label>Environment</Label>
                  <select className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                    <option value="live">Live</option>
                    <option value="sandbox">Sandbox</option>
                  </select>
                </div>
                {accountId && (
                  <div className="text-sm text-green-700 bg-green-50 rounded-md p-2">
                    Account: {accountId}
                  </div>
                )}
                {renderStatus()}
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => handleTest("/tradier/test", { access_token: apiKey, environment: env })} disabled={!apiKey || loading}>
                    Test Connection
                  </Button>
                  <Button className="flex-1" onClick={() => handleSync("/tradier/sync", { access_token: apiKey, tradier_account_id: accountId, environment: env })} disabled={!apiKey || !accountId || loading}>
                    {loading ? "Importing..." : "Import Positions"}
                  </Button>
                </div>
                {renderSyncResult()}
              </CardContent>
            </Card>
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}

        {/* Crypto Wallet */}
        {step === "crypto" && portfolio && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Connect Crypto Wallet</CardTitle>
                <CardDescription>
                  Paste your ETH (0x...) or BTC wallet address to read on-chain balances
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Wallet Address</Label>
                  <Input value={walletAddress} onChange={(e) => setWalletAddress(e.target.value)} placeholder="0x... or bc1..." className="font-mono text-sm" />
                </div>
                {renderStatus()}
                <div className="flex gap-2">
                  <Button variant="outline" className="flex-1" onClick={() => handleTest("/crypto-wallet/test", { address: walletAddress })} disabled={!walletAddress || loading}>
                    Scan Wallet
                  </Button>
                  <Button className="flex-1" onClick={() => handleSync("/crypto-wallet/sync", { address: walletAddress })} disabled={!walletAddress || loading}>
                    {loading ? "Importing..." : "Import Holdings"}
                  </Button>
                </div>
                {renderSyncResult()}
              </CardContent>
            </Card>
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}

        {step === "manual" && portfolio && (
          <div className="space-y-4">
            <AddPositionForm portfolioId={portfolio.id} onDone={handleDone} />
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}

        {step === "csv" && portfolio && (
          <div className="space-y-4">
            <CsvUploadWizard portfolioId={portfolio.id} onDone={handleDone} />
            <Button variant="ghost" className="w-full" onClick={goBack}>Back</Button>
          </div>
        )}
      </div>
    </div>
  );
}
