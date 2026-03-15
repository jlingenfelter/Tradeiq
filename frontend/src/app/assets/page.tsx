"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useAssets, useCreateAsset, useUpdateAsset, useDeleteAsset, useLiabilities, useCreateLiability } from "@/hooks/use-wealth";
import { formatCurrency } from "@/lib/utils";
import { Plus, Trash2, Pencil, X, Check, LinkIcon } from "lucide-react";
import { ASSET_CLASSES, LIQUIDITY_CATEGORIES, LIABILITY_TYPES } from "@/types";
import type { Asset } from "@/types";

const LIABILITY_LABELS: Record<string, string> = {
  mortgage: "Mortgage", loan: "Loan", credit_card: "Credit Card",
  tax: "Tax", margin: "Margin", business_debt: "Business Debt", other: "Other",
};

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
  const updateAsset = useUpdateAsset();
  const deleteAsset = useDeleteAsset();
  const { data: liabilities } = useLiabilities();
  const createLiability = useCreateLiability();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ name: "", current_value: "", currency: "", liquidity_category: "", country: "", notes: "", asset_class: "" });
  const [linkingAssetId, setLinkingAssetId] = useState<string | null>(null);
  const [liabilityForm, setLiabilityForm] = useState({ name: "", liability_type: "mortgage", current_balance: "", interest_rate: "", monthly_payment: "", notes: "" });
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
                    {(() => {
                      const byCurrency: Record<string, number> = {};
                      items.forEach((a) => { byCurrency[a.currency] = (byCurrency[a.currency] || 0) + a.current_value; });
                      return Object.entries(byCurrency).map(([cur, val]) => formatCurrency(val, cur)).join(" + ");
                    })()}
                  </span>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {items.map((asset) => (
                    editingId === asset.id ? (
                      <div key={asset.id} className="rounded-md border border-indigo-200 bg-indigo-50/30 px-4 py-3 space-y-3">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <div>
                            <Label className="text-xs">Name</Label>
                            <Input value={editForm.name} onChange={(e) => setEditForm({ ...editForm, name: e.target.value })} className="h-8 text-sm" />
                          </div>
                          <div>
                            <Label className="text-xs">Value</Label>
                            <Input type="number" step="0.01" value={editForm.current_value} onChange={(e) => setEditForm({ ...editForm, current_value: e.target.value })} className="h-8 text-sm" />
                          </div>
                          <div>
                            <Label className="text-xs">Currency</Label>
                            <Input value={editForm.currency} onChange={(e) => setEditForm({ ...editForm, currency: e.target.value })} className="h-8 text-sm" />
                          </div>
                          <div>
                            <Label className="text-xs">Asset Class</Label>
                            <select className="w-full rounded-md border px-2 py-1.5 text-sm" value={editForm.asset_class} onChange={(e) => setEditForm({ ...editForm, asset_class: e.target.value })}>
                              {ASSET_CLASSES.map((cls) => <option key={cls} value={cls}>{CLASS_LABELS[cls]}</option>)}
                            </select>
                          </div>
                          <div>
                            <Label className="text-xs">Liquidity</Label>
                            <select className="w-full rounded-md border px-2 py-1.5 text-sm" value={editForm.liquidity_category} onChange={(e) => setEditForm({ ...editForm, liquidity_category: e.target.value })}>
                              {LIQUIDITY_CATEGORIES.map((liq) => <option key={liq} value={liq}>{LIQUIDITY_LABELS[liq]}</option>)}
                            </select>
                          </div>
                          <div>
                            <Label className="text-xs">Country</Label>
                            <Input value={editForm.country} onChange={(e) => setEditForm({ ...editForm, country: e.target.value })} className="h-8 text-sm" />
                          </div>
                          <div className="md:col-span-2">
                            <Label className="text-xs">Notes</Label>
                            <Input value={editForm.notes} onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })} className="h-8 text-sm" />
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" onClick={async () => {
                            await updateAsset.mutateAsync({
                              id: asset.id,
                              name: editForm.name,
                              current_value: parseFloat(editForm.current_value) || asset.current_value,
                              currency: editForm.currency,
                              asset_class: editForm.asset_class,
                              liquidity_category: editForm.liquidity_category,
                              country: editForm.country || undefined,
                              notes: editForm.notes || undefined,
                            } as any);
                            setEditingId(null);
                          }} disabled={updateAsset.isPending}>
                            <Check className="h-3.5 w-3.5 mr-1" />
                            {updateAsset.isPending ? "Saving..." : "Save"}
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div key={asset.id} className="space-y-0">
                        <div className="flex items-center justify-between rounded-md border px-4 py-3">
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
                            {/* Show linked liabilities */}
                            {liabilities?.filter((l) => l.linked_asset_id === asset.id).map((l) => (
                              <div key={l.id} className="flex items-center gap-2 mt-1.5">
                                <LinkIcon className="h-3 w-3 text-red-400" />
                                <span className="text-xs text-red-600 font-medium">
                                  {l.name}: {formatCurrency(l.current_balance, l.currency)}
                                </span>
                                {l.interest_rate && (
                                  <span className="text-xs text-neutral-400">{l.interest_rate}% APR</span>
                                )}
                              </div>
                            ))}
                          </div>
                          <div className="flex items-center gap-3">
                            <div className="text-right">
                              <span className="text-sm font-medium">
                                {formatCurrency(asset.current_value, asset.currency)}
                              </span>
                              {(() => {
                                const linked = liabilities?.filter((l) => l.linked_asset_id === asset.id) ?? [];
                                const totalDebt = linked.reduce((sum, l) => sum + l.current_balance, 0);
                                if (totalDebt > 0) {
                                  const equity = asset.current_value - totalDebt;
                                  return (
                                    <div className="text-xs text-neutral-500">
                                      Equity: {formatCurrency(equity, asset.currency)}
                                    </div>
                                  );
                                }
                                return null;
                              })()}
                            </div>
                            <Button
                              variant="ghost" size="sm"
                              title="Link a liability"
                              onClick={() => {
                                setLinkingAssetId(linkingAssetId === asset.id ? null : asset.id);
                                setLiabilityForm({ name: `${asset.name} Mortgage`, liability_type: "mortgage", current_balance: "", interest_rate: "", monthly_payment: "", notes: "" });
                              }}
                            >
                              <LinkIcon className="h-3.5 w-3.5 text-blue-500" />
                            </Button>
                            <Button
                              variant="ghost" size="sm"
                              onClick={() => {
                                setEditingId(asset.id);
                                setEditForm({
                                  name: asset.name,
                                  current_value: String(asset.current_value),
                                  currency: asset.currency,
                                  liquidity_category: asset.liquidity_category,
                                  country: asset.country || "",
                                  notes: asset.notes || "",
                                  asset_class: asset.asset_class,
                                });
                              }}
                            >
                              <Pencil className="h-3.5 w-3.5 text-neutral-400" />
                            </Button>
                            <Button
                              variant="ghost" size="sm"
                              onClick={() => {
                                if (confirm("Delete this asset?")) deleteAsset.mutate(asset.id);
                              }}
                            >
                              <Trash2 className="h-3.5 w-3.5 text-red-500" />
                            </Button>
                          </div>
                        </div>
                        {/* Inline liability form */}
                        {linkingAssetId === asset.id && (
                          <div className="rounded-b-md border border-t-0 border-blue-200 bg-blue-50/30 px-4 py-3 space-y-3">
                            <p className="text-xs font-medium text-blue-700">Link a liability to {asset.name}</p>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                              <div>
                                <Label className="text-xs">Name</Label>
                                <Input value={liabilityForm.name} onChange={(e) => setLiabilityForm({ ...liabilityForm, name: e.target.value })} className="h-8 text-sm" />
                              </div>
                              <div>
                                <Label className="text-xs">Type</Label>
                                <select className="w-full rounded-md border px-2 py-1.5 text-sm" value={liabilityForm.liability_type} onChange={(e) => setLiabilityForm({ ...liabilityForm, liability_type: e.target.value })}>
                                  {LIABILITY_TYPES.map((t) => <option key={t} value={t}>{LIABILITY_LABELS[t] || t}</option>)}
                                </select>
                              </div>
                              <div>
                                <Label className="text-xs">Balance Owed *</Label>
                                <Input type="number" step="0.01" value={liabilityForm.current_balance} onChange={(e) => setLiabilityForm({ ...liabilityForm, current_balance: e.target.value })} className="h-8 text-sm" placeholder="e.g. 250000" />
                              </div>
                              <div>
                                <Label className="text-xs">Interest Rate %</Label>
                                <Input type="number" step="0.01" value={liabilityForm.interest_rate} onChange={(e) => setLiabilityForm({ ...liabilityForm, interest_rate: e.target.value })} className="h-8 text-sm" placeholder="e.g. 4.5" />
                              </div>
                              <div>
                                <Label className="text-xs">Monthly Payment</Label>
                                <Input type="number" step="0.01" value={liabilityForm.monthly_payment} onChange={(e) => setLiabilityForm({ ...liabilityForm, monthly_payment: e.target.value })} className="h-8 text-sm" />
                              </div>
                              <div>
                                <Label className="text-xs">Notes</Label>
                                <Input value={liabilityForm.notes} onChange={(e) => setLiabilityForm({ ...liabilityForm, notes: e.target.value })} className="h-8 text-sm" />
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button size="sm" onClick={async () => {
                                await createLiability.mutateAsync({
                                  name: liabilityForm.name,
                                  liability_type: liabilityForm.liability_type,
                                  current_balance: parseFloat(liabilityForm.current_balance) || 0,
                                  currency: asset.currency,
                                  interest_rate: liabilityForm.interest_rate ? parseFloat(liabilityForm.interest_rate) : undefined,
                                  monthly_payment: liabilityForm.monthly_payment ? parseFloat(liabilityForm.monthly_payment) : undefined,
                                  linked_asset_id: asset.id,
                                  notes: liabilityForm.notes || undefined,
                                } as any);
                                setLinkingAssetId(null);
                              }} disabled={createLiability.isPending || !liabilityForm.current_balance}>
                                <Check className="h-3.5 w-3.5 mr-1" />
                                {createLiability.isPending ? "Saving..." : "Link Liability"}
                              </Button>
                              <Button size="sm" variant="ghost" onClick={() => setLinkingAssetId(null)}>
                                Cancel
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    )
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
