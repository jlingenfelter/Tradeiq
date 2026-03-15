"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useLiabilities, useCreateLiability, useDeleteLiability } from "@/hooks/use-wealth";
import { formatCurrency } from "@/lib/utils";
import { Plus, Trash2, X } from "lucide-react";
import { LIABILITY_TYPES } from "@/types";

const TYPE_LABELS: Record<string, string> = {
  mortgage: "Mortgage", loan: "Loan", credit_card: "Credit Card",
  tax: "Tax Liability", margin: "Margin Debt", business_debt: "Business Debt", other: "Other",
};

export default function LiabilitiesPage() {
  const { data: liabilities, isLoading } = useLiabilities();
  const createLiability = useCreateLiability();
  const deleteLiability = useDeleteLiability();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", liability_type: "mortgage", current_balance: "",
    currency: "USD", interest_rate: "", monthly_payment: "", notes: "",
  });

  const totalDebt = liabilities?.reduce((sum, l) => sum + l.current_balance, 0) || 0;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await createLiability.mutateAsync({
      name: form.name,
      liability_type: form.liability_type,
      current_balance: parseFloat(form.current_balance) || 0,
      currency: form.currency,
      interest_rate: form.interest_rate ? parseFloat(form.interest_rate) : undefined,
      monthly_payment: form.monthly_payment ? parseFloat(form.monthly_payment) : undefined,
      notes: form.notes || undefined,
    } as any);
    setShowForm(false);
    setForm({
      name: "", liability_type: "mortgage", current_balance: "",
      currency: "USD", interest_rate: "", monthly_payment: "", notes: "",
    });
  }

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Liabilities</h2>
            <p className="text-sm text-neutral-500">
              Track debts and obligations · Total: {formatCurrency(totalDebt)}
            </p>
          </div>
          <Button onClick={() => setShowForm(!showForm)}>
            {showForm ? <X className="h-4 w-4 mr-1" /> : <Plus className="h-4 w-4 mr-1" />}
            {showForm ? "Cancel" : "Add Liability"}
          </Button>
        </div>

        {showForm && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Add New Liability</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label>Name *</Label>
                  <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </div>
                <div>
                  <Label>Type *</Label>
                  <select
                    className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm"
                    value={form.liability_type}
                    onChange={(e) => setForm({ ...form, liability_type: e.target.value })}
                  >
                    {LIABILITY_TYPES.map((t) => (
                      <option key={t} value={t}>{TYPE_LABELS[t]}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>Balance *</Label>
                  <Input type="number" step="0.01" value={form.current_balance}
                    onChange={(e) => setForm({ ...form, current_balance: e.target.value })} required />
                </div>
                <div>
                  <Label>Currency</Label>
                  <Input value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
                </div>
                <div>
                  <Label>Interest Rate (%)</Label>
                  <Input type="number" step="0.01" value={form.interest_rate}
                    onChange={(e) => setForm({ ...form, interest_rate: e.target.value })} />
                </div>
                <div>
                  <Label>Monthly Payment</Label>
                  <Input type="number" step="0.01" value={form.monthly_payment}
                    onChange={(e) => setForm({ ...form, monthly_payment: e.target.value })} />
                </div>
                <div className="md:col-span-2">
                  <Label>Notes</Label>
                  <Input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
                </div>
                <div className="flex items-end">
                  <Button type="submit" disabled={createLiability.isPending} className="w-full">
                    {createLiability.isPending ? "Adding..." : "Add Liability"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {isLoading ? (
          <div className="text-neutral-500">Loading liabilities...</div>
        ) : !liabilities || liabilities.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center text-neutral-500">
              No liabilities found. Add your debts to get a complete wealth picture.
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent className="p-0">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left">
                    <th className="px-4 py-3 text-xs font-medium text-neutral-500">Name</th>
                    <th className="px-4 py-3 text-xs font-medium text-neutral-500">Type</th>
                    <th className="px-4 py-3 text-xs font-medium text-neutral-500 text-right">Balance</th>
                    <th className="px-4 py-3 text-xs font-medium text-neutral-500 text-right">Rate</th>
                    <th className="px-4 py-3 text-xs font-medium text-neutral-500 text-right">Monthly</th>
                    <th className="px-4 py-3 text-xs font-medium text-neutral-500"></th>
                  </tr>
                </thead>
                <tbody>
                  {liabilities.map((l) => (
                    <tr key={l.id} className="border-b last:border-0 hover:bg-neutral-50">
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium">{l.name}</div>
                        {l.notes && <div className="text-xs text-neutral-500">{l.notes}</div>}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="secondary">{TYPE_LABELS[l.liability_type] || l.liability_type}</Badge>
                      </td>
                      <td className="px-4 py-3 text-right text-sm font-medium text-red-600">
                        {formatCurrency(l.current_balance, l.currency)}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-neutral-600">
                        {l.interest_rate ? `${l.interest_rate}%` : "—"}
                      </td>
                      <td className="px-4 py-3 text-right text-sm text-neutral-600">
                        {l.monthly_payment ? formatCurrency(l.monthly_payment, l.currency) : "—"}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Button variant="ghost" size="sm"
                          onClick={() => {
                            if (confirm("Delete this liability?")) deleteLiability.mutate(l.id);
                          }}>
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
