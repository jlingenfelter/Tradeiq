"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAssets, useCreateAsset, useDeleteAsset } from "@/hooks/use-wealth";
import { formatCurrency } from "@/lib/utils";
import { Plus, Trash2, X } from "lucide-react";
import { ASSET_CLASSES, LIQUIDITY_CATEGORIES } from "@/types";
import type { Asset } from "@/types";

const CLASS_LABELS: Record<string, string> = {
  cash: "Cash", stock: "Stocks", etf: "ETFs", mutual_fund: "Mutual Funds",
  bond: "Bonds", pension: "Pensions", crypto: "Crypto", property: "Property",
  business_equity: "Business Equity", gold: "Gold", watch: "Watches",
  collectible: "Collectibles", private_loan_receivable: "Private Loans", other: "Other",
};

const LIQUIDITY_LABELS: Record<string, string> = {
  highly_liquid: "Highly Liquid", liquid: "Liquid",
  semi_liquid: "Semi-Liquid", illiquid: "Illiquid",
};

export default function AssetsPage() {
  const { data: assets, isLoading } = useAssets();
  const createAsset = useCreateAsset();
  const deleteAsset = useDeleteAsset();
  const [showForm, setShowForm] = useState(false);
  const [filter, setFilter] = useState<string>("");
  const [form, setForm] = useState({
    name: "", asset_class: "cash", current_value: "",
    currency: "USD", liquidity_category: "liquid",
    symbol: "", quantity: "", unit_value: "", cost_basis: "",
    country: "", sector: "", notes: "", valuation_source: "manual",
  });

  const filtered = assets?.filter((a) =>
    !filter || a.asset_class === filter
  );

  // Group by category
  const grouped: Record<string, Asset[]> = {};
  filtered?.forEach((a) => {
    const cat = CLASS_LABELS[a.asset_class] || a.asset_class;
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(a);
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await createAsset.mutateAsync({
      name: form.name,
      asset_class: form.asset_class,
      current_value: parseFloat(form.current_value) || 0,
      currency: form.currency,
      liquidity_category: form.liquidity_category,
      symbol: form.symbol || undefined,
      quantity: form.quantity ? parseFloat(form.quantity) : undefined,
      unit_value: form.unit_value ? parseFloat(form.unit_value) : undefined,
      cost_basis: form.cost_basis ? parseFloat(form.cost_basis) : undefined,
      country: form.country || undefined,
      sector: form.sector || undefined,
      notes: form.notes || undefined,
      valuation_source: form.valuation_source,
    } as any);
    setShowForm(false);
    setForm({
      name: "", asset_class: "cash", current_value: "",
      currency: "USD", liquidity_category: "liquid",
      symbol: "", quantity: "", unit_value: "", cost_basis: "",
      country: "", sector: "", notes: "", valuation_source: "manual",
    });
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Assets</h2>
            <p className="text-sm text-neutral-500">Track all your assets across categories</p>
          </div>
          <Button onClick={() => setShowForm(!showForm)}>
            {showForm ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
            {showForm ? "Cancel" : "Add Asset"}
          </Button>
        </div>

        {/* Filter pills */}
        <div className="flex gap-2 flex-wrap">
          <button
            className={`px-3 py-1 text-xs rounded-full border transition-colors ${!filter ? "bg-neutral-900 text-white border-neutral-900" : "border-neutral-200 hover:bg-neutral-50"}`}
            onClick={() => setFilter("")}
          >
            All
          </button>
          {ASSET_CLASSES.map((cls) => (
            <button
              key={cls}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${filter === cls ? "bg-neutral-900 text-white border-neutral-900" : "border-neutral-200 hover:bg-neutral-50"}`}
              onClick={() => setFilter(cls)}
            >
              {CLASS_LABELS[cls] || cls}
            </button>
          ))}
        </div>

        {/* Add form */}
        {showForm && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Add New Asset</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label>Name *</Label>
                  <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </div>
                <div>
                  <Label>Asset Class *</Label>
                  <select
                    className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                    value={form.asset_class}
                    onChange={(e) => setForm({ ...form, asset_class: e.target.value })}
                  >
                    {ASSET_CLASSES.map((cls) => (
                      <option key={cls} value={cls}>{CLASS_LABELS[cls]}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>Current Value *</Label>
                  <Input type="number" step="0.01" value={form.current_value}
                    onChange={(e) => setForm({ ...form, current_value: e.target.value })} required />
                </div>
                <div>
                  <Label>Currency</Label>
                  <Input value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
                </div>
                <div>
                  <Label>Liquidity</Label>
                  <select
                    className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                    value={form.liquidity_category}
                    onChange={(e) => setForm({ ...form, liquidity_category: e.target.value })}
                  >
                    {LIQUIDITY_CATEGORIES.map((liq) => (
                      <option key={liq} value={liq}>{LIQUIDITY_LABELS[liq]}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>Symbol (if applicable)</Label>
                  <Input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} />
                </div>
                <div>
                  <Label>Quantity</Label>
                  <Input type="number" step="any" value={form.quantity}
                    onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
                </div>
                <div>
                  <Label>Cost Basis</Label>
                  <Input type="number" step="0.01" value={form.cost_basis}
                    onChange={(e) => setForm({ ...form, cost_basis: e.target.value })} />
                </div>
                <div>
                  <Label>Country</Label>
                  <Input value={form.country} onChange={(e) => setForm({ ...form, country: e.target.value })} />
                </div>
                <div className="md:col-span-2">
                  <Label>Notes</Label>
                  <Input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                </div>
                <div className="flex items-end">
                  <Button type="submit" disabled={createAsset.isPending} className="w-full">
                    {createAsset.isPending ? "Adding..." : "Add Asset"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Asset list grouped by category */}
        {isLoading ? (
          <div className="text-neutral-500">Loading assets...</div>
        ) : Object.keys(grouped).length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-neutral-500">
              No assets found. Add your first asset to get started.
            </CardContent>
          </Card>
        ) : (
          Object.entries(grouped).map(([category, items]) => (
            <Card key={category}>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{category}</CardTitle>
                  <span className="text-sm text-neutral-500">
                    {formatCurrency(items.reduce((sum, a) => sum + a.current_value, 0))}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {items.map((asset) => (
                    <div key={asset.id} className="flex items-center justify-between rounded-md border px-4 py-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{asset.name}</span>
                          {asset.symbol && (
                            <Badge variant="secondary" className="text-xs">{asset.symbol}</Badge>
                          )}
                          <Badge variant="secondary" className="text-xs">
                            {LIQUIDITY_LABELS[asset.liquidity_category] || asset.liquidity_category}
                          </Badge>
                        </div>
                        <div className="text-xs text-neutral-500 mt-0.5">
                          {asset.currency}
                          {asset.country ? ` · ${asset.country}` : ""}
                          {asset.notes ? ` · ${asset.notes}` : ""}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-medium">
                          {formatCurrency(asset.current_value, asset.currency)}
                        </span>
                        <Button
                          variant="ghost" size="sm"
                          onClick={() => {
                            if (confirm("Delete this asset?")) deleteAsset.mutate(asset.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </AppShell>
  );
}
