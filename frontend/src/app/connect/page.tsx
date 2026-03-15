"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePortfolios } from "@/hooks/use-portfolio";
import { useConnections } from "@/hooks/use-analytics";
import { api } from "@/lib/api";
import { ArrowLeft, Check, Loader2, RefreshCw, Trash2, Wifi } from "lucide-react";

type Broker = "trading212" | "alpaca" | "ibkr" | "ig" | "tradier" | "crypto" | null;

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

const BROKERS = [
  { id: "trading212" as Broker, name: "Trading 212", desc: "Auto-import via API key", category: "broker" },
  { id: "alpaca" as Broker, name: "Alpaca", desc: "Connect with API key and secret", category: "broker" },
  { id: "ibkr" as Broker, name: "Interactive Brokers", desc: "Connect via IB Gateway", category: "broker" },
  { id: "ig" as Broker, name: "IG Group", desc: "Connect with API key and credentials", category: "broker" },
  { id: "tradier" as Broker, name: "Tradier", desc: "Connect with OAuth access token", category: "broker" },
  { id: "crypto" as Broker, name: "Crypto Wallet", desc: "Read ETH or BTC wallet balances", category: "crypto" },
];

export default function ConnectPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: portfolios } = usePortfolios();
  const [selectedBroker, setSelectedBroker] = useState<Broker>(null);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  // Broker fields
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [env, setEnv] = useState("live");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [gatewayUrl, setGatewayUrl] = useState("https://localhost:5000");
  const [accountId, setAccountId] = useState("");
  const [walletAddress, setWalletAddress] = useState("");
  const [igToken, setIgToken] = useState("");
  const [igCst, setIgCst] = useState("");

  // Set first portfolio as default
  if (portfolios && portfolios.length > 0 && !selectedPortfolioId) {
    setSelectedPortfolioId(portfolios[0].id);
  }

  const { data: connections, refetch: refetchConnections } = useConnections(selectedPortfolioId);

  async function handleResync(connectionId: string) {
    setSyncingId(connectionId);
    try {
      await api.post(`/connections/${connectionId}/sync`);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["analytics"] });
      queryClient.invalidateQueries({ queryKey: ["connections"] });
      queryClient.invalidateQueries({ queryKey: ["wealth-dashboard"] });
      refetchConnections();
    } catch (err) {
      console.error("Sync failed:", err);
    } finally {
      setSyncingId(null);
    }
  }

  async function handleDisconnect(connectionId: string, name: string) {
    if (!confirm(`Disconnect "${name}"? This will stop auto-syncing but keep existing positions.`)) return;
    try {
      await api.delete(`/connections/${connectionId}`);
      refetchConnections();
    } catch (err) {
      console.error("Disconnect failed:", err);
    }
  }

  function resetFields() {
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
    resetFields();
    setSelectedBroker(null);
  }

  async function handleTest(endpoint: string, body: Record<string, unknown>) {
    setStatus("Testing connection...");
    try {
      const res = await api.post<TestResult>(endpoint, body);
      if (res.success) {
        setStatus(res.message || "Connected successfully");
        if ("access_token" in res && res.access_token) {
          setIgToken(res.access_token as string);
          setIgCst((res.cst as string) || "");
          if (res.account_id) setAccountId(res.account_id as string);
        }
        if ("accounts" in res && Array.isArray(res.accounts) && res.accounts.length > 0) {
          setAccountId(res.accounts[0]);
        }
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
    if (!selectedPortfolioId) {
      setStatus("Error: Please select a portfolio first");
      return;
    }
    setLoading(true);
    setStatus("Importing positions...");
    try {
      const result = await api.post<SyncResult>(endpoint, { ...body, portfolio_id: selectedPortfolioId });
      setSyncResult(result);
      const extra = result.chain ? ` from ${result.chain}` : "";
      if (result.imported === 0) {
        const errMsg = result.errors.length > 0 ? result.errors[0] : "No positions found to import";
        setStatus(`Error: ${errMsg}`);
      } else {
        setStatus(`Imported ${result.imported} positions${extra}`);
        // Invalidate caches so fresh data loads
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
        queryClient.invalidateQueries({ queryKey: ["analytics"] });
        queryClient.invalidateQueries({ queryKey: ["positions"] });
        queryClient.invalidateQueries({ queryKey: ["connections"] });
        queryClient.invalidateQueries({ queryKey: ["wealth-dashboard"] });
      }
    } catch (err: unknown) {
      setStatus(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setLoading(false);
    }
  }

  const isError = status.startsWith("Error") || status.includes("failed") || status.includes("Invalid");
  const isSuccess = status.startsWith("Connected") || status.startsWith("Imported") || status.startsWith("Found") || status.startsWith("Authenticated");

  function renderStatus() {
    if (!status) return null;
    return (
      <div className={`rounded-lg p-3 text-sm ${
        isError ? "bg-red-50 text-red-700"
          : isSuccess ? "bg-emerald-50 text-emerald-700"
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
        <div className="flex items-center gap-2 text-sm text-emerald-700">
          <Check className="h-4 w-4" />
          {syncResult.imported} positions imported
          {syncResult.skipped > 0 && `, ${syncResult.skipped} skipped`}
        </div>
        {syncResult.errors.length > 0 && (
          <div className="text-xs text-red-600">
            {syncResult.errors.map((e, i) => <div key={i}>{e}</div>)}
          </div>
        )}
        <Button onClick={() => router.push("/dashboard")} className="w-full bg-indigo-600 hover:bg-indigo-700">
          Go to Dashboard
        </Button>
      </div>
    );
  }

  function renderPortfolioSelector() {
    if (!portfolios || portfolios.length === 0) return null;
    return (
      <div className="space-y-2">
        <Label>Target Portfolio</Label>
        <select
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
          value={selectedPortfolioId}
          onChange={(e) => setSelectedPortfolioId(e.target.value)}
        >
          {portfolios.map((p) => (
            <option key={p.id} value={p.id}>{p.name} ({p.base_currency})</option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <AppShell>
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Connect Accounts</h2>
          <p className="text-sm text-slate-500 mt-1">Link your broker accounts and crypto wallets to import positions automatically</p>
        </div>

        {/* Saved Connections */}
        {!selectedBroker && connections && connections.length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Active Connections</CardTitle>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    setSyncingId("all");
                    try {
                      await api.post(`/portfolios/${selectedPortfolioId}/connections/sync-all`);
                      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
                      queryClient.invalidateQueries({ queryKey: ["analytics"] });
                      queryClient.invalidateQueries({ queryKey: ["wealth-dashboard"] });
                      refetchConnections();
                    } finally {
                      setSyncingId(null);
                    }
                  }}
                  disabled={syncingId !== null}
                >
                  <RefreshCw className={`h-3.5 w-3.5 mr-1 ${syncingId === "all" ? "animate-spin" : ""}`} />
                  Sync All
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {portfolios && portfolios.length > 1 && (
                  <select
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm mb-3"
                    value={selectedPortfolioId}
                    onChange={(e) => setSelectedPortfolioId(e.target.value)}
                  >
                    {portfolios.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} ({p.base_currency})</option>
                    ))}
                  </select>
                )}
                {connections.map((conn) => (
                  <div key={conn.id} className="flex items-center gap-3 rounded-lg border border-slate-200 px-4 py-3">
                    <Wifi className={`h-4 w-4 ${conn.sync_error ? "text-red-500" : "text-emerald-500"}`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-900">{conn.name}</div>
                      <div className="text-xs text-slate-500">
                        {conn.position_count} positions
                        {conn.last_synced_at && ` · Last synced ${new Date(conn.last_synced_at).toLocaleString()}`}
                      </div>
                      {conn.sync_error && (
                        <div className="text-xs text-red-600 mt-0.5 truncate">{conn.sync_error}</div>
                      )}
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleResync(conn.id)}
                      disabled={syncingId !== null}
                    >
                      <RefreshCw className={`h-3.5 w-3.5 ${syncingId === conn.id ? "animate-spin" : ""}`} />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDisconnect(conn.id, conn.name)}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-red-500" />
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {!selectedBroker && (
          <div className="space-y-4">
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Add New Connection</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {BROKERS.filter(b => b.category === "broker").map((broker) => (
                  <Card key={broker.id} className="cursor-pointer hover:border-indigo-300 hover:shadow-md" onClick={() => setSelectedBroker(broker.id)}>
                    <CardContent className="p-4">
                      <div className="font-medium text-sm text-slate-900">{broker.name}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{broker.desc}</div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Crypto Wallets</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {BROKERS.filter(b => b.category === "crypto").map((broker) => (
                  <Card key={broker.id} className="cursor-pointer hover:border-indigo-300 hover:shadow-md" onClick={() => setSelectedBroker(broker.id)}>
                    <CardContent className="p-4">
                      <div className="font-medium text-sm text-slate-900">{broker.name}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{broker.desc}</div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Trading 212 */}
        {selectedBroker === "trading212" && (
          <Card>
            <CardHeader>
              <CardTitle>Connect Trading 212</CardTitle>
              <CardDescription>Enter your API key and secret from Trading 212 Settings &rarr; API (Beta)</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {renderPortfolioSelector()}
              <div className="space-y-2">
                <Label>API Key</Label>
                <Input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Paste your Trading 212 API key" />
              </div>
              <div className="space-y-2">
                <Label>API Secret</Label>
                <Input type="password" value={apiSecret} onChange={(e) => setApiSecret(e.target.value)} placeholder="Paste your Trading 212 API secret" />
              </div>
              <div className="space-y-2">
                <Label>Environment</Label>
                <select className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                  <option value="live">Live (Real Money)</option>
                  <option value="demo">Demo (Paper Trading)</option>
                </select>
              </div>
              {renderStatus()}
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => handleTest("/trading212/test", { api_key: apiKey, api_secret: apiSecret, environment: env })} disabled={!apiKey || !apiSecret || loading}>
                  Test Connection
                </Button>
                <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => handleSync("/trading212/sync", { api_key: apiKey, api_secret: apiSecret, environment: env })} disabled={!apiKey || !apiSecret || loading}>
                  {loading ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Importing...</> : "Import Positions"}
                </Button>
              </div>
              {renderSyncResult()}
            </CardContent>
          </Card>
        )}

        {/* Alpaca */}
        {selectedBroker === "alpaca" && (
          <Card>
            <CardHeader>
              <CardTitle>Connect Alpaca</CardTitle>
              <CardDescription>Enter your API key and secret from the Alpaca dashboard</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {renderPortfolioSelector()}
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
                <select className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                  <option value="live">Live</option>
                  <option value="paper">Paper Trading</option>
                </select>
              </div>
              {renderStatus()}
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => handleTest("/alpaca/test", { api_key: apiKey, api_secret: apiSecret, environment: env })} disabled={!apiKey || !apiSecret || loading}>
                  Test Connection
                </Button>
                <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => handleSync("/alpaca/sync", { api_key: apiKey, api_secret: apiSecret, environment: env })} disabled={!apiKey || !apiSecret || loading}>
                  {loading ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Importing...</> : "Import Positions"}
                </Button>
              </div>
              {renderSyncResult()}
            </CardContent>
          </Card>
        )}

        {/* Interactive Brokers */}
        {selectedBroker === "ibkr" && (
          <Card>
            <CardHeader>
              <CardTitle>Connect Interactive Brokers</CardTitle>
              <CardDescription>Requires IB Gateway or Client Portal API running locally</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {renderPortfolioSelector()}
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
                <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => handleSync("/ibkr/sync", { gateway_url: gatewayUrl, ibkr_account_id: accountId })} disabled={!accountId || loading}>
                  {loading ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Importing...</> : "Import Positions"}
                </Button>
              </div>
              {renderSyncResult()}
            </CardContent>
          </Card>
        )}

        {/* IG Group */}
        {selectedBroker === "ig" && (
          <Card>
            <CardHeader>
              <CardTitle>Connect IG Group</CardTitle>
              <CardDescription>Enter your IG API key and login credentials</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {renderPortfolioSelector()}
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
                <select className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                  <option value="live">Live</option>
                  <option value="demo">Demo</option>
                </select>
              </div>
              {renderStatus()}
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => handleTest("/ig/test", { api_key: apiKey, username, password, environment: env })} disabled={!apiKey || !username || !password || loading}>
                  Authenticate
                </Button>
                <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => handleSync("/ig/sync", { api_key: apiKey, access_token: igToken, cst: igCst, environment: env })} disabled={!igToken || loading}>
                  {loading ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Importing...</> : "Import Positions"}
                </Button>
              </div>
              {renderSyncResult()}
            </CardContent>
          </Card>
        )}

        {/* Tradier */}
        {selectedBroker === "tradier" && (
          <Card>
            <CardHeader>
              <CardTitle>Connect Tradier</CardTitle>
              <CardDescription>Enter your Tradier OAuth access token</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {renderPortfolioSelector()}
              <div className="space-y-2">
                <Label>Access Token</Label>
                <Input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Tradier access token" />
              </div>
              <div className="space-y-2">
                <Label>Environment</Label>
                <select className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" value={env} onChange={(e) => setEnv(e.target.value)}>
                  <option value="live">Live</option>
                  <option value="sandbox">Sandbox</option>
                </select>
              </div>
              {accountId && (
                <div className="text-sm text-emerald-700 bg-emerald-50 rounded-lg p-2">
                  Account: {accountId}
                </div>
              )}
              {renderStatus()}
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => handleTest("/tradier/test", { access_token: apiKey, environment: env })} disabled={!apiKey || loading}>
                  Test Connection
                </Button>
                <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => handleSync("/tradier/sync", { access_token: apiKey, tradier_account_id: accountId, environment: env })} disabled={!apiKey || !accountId || loading}>
                  {loading ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Importing...</> : "Import Positions"}
                </Button>
              </div>
              {renderSyncResult()}
            </CardContent>
          </Card>
        )}

        {/* Crypto Wallet */}
        {selectedBroker === "crypto" && (
          <Card>
            <CardHeader>
              <CardTitle>Connect Crypto Wallet</CardTitle>
              <CardDescription>Paste your ETH (0x...) or BTC wallet address to read on-chain balances</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {renderPortfolioSelector()}
              <div className="space-y-2">
                <Label>Wallet Address</Label>
                <Input value={walletAddress} onChange={(e) => setWalletAddress(e.target.value)} placeholder="0x... or bc1..." className="font-mono text-sm" />
              </div>
              {renderStatus()}
              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => handleTest("/crypto-wallet/test", { address: walletAddress })} disabled={!walletAddress || loading}>
                  Scan Wallet
                </Button>
                <Button className="flex-1 bg-indigo-600 hover:bg-indigo-700" onClick={() => handleSync("/crypto-wallet/sync", { address: walletAddress })} disabled={!walletAddress || loading}>
                  {loading ? <><Loader2 className="h-4 w-4 mr-1 animate-spin" /> Importing...</> : "Import Holdings"}
                </Button>
              </div>
              {renderSyncResult()}
            </CardContent>
          </Card>
        )}

        {selectedBroker && (
          <Button variant="ghost" className="w-full" onClick={goBack}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to all integrations
          </Button>
        )}
      </div>
    </AppShell>
  );
}
