"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import type { Position } from "@/types";

interface Props {
  portfolioId: string;
  onDone: () => void;
}

export function AddPositionForm({ portfolioId, onDone }: Props) {
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [quantity, setQuantity] = useState("");
  const [costBasis, setCostBasis] = useState("");
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const pos = await api.post<Position>(`/portfolios/${portfolioId}/positions`, {
        symbol: symbol.toUpperCase(),
        asset_name: name || symbol.toUpperCase(),
        quantity: parseFloat(quantity),
        cost_basis_per_share: costBasis ? parseFloat(costBasis) : null,
      });
      setPositions([...positions, pos]);
      setSymbol("");
      setName("");
      setQuantity("");
      setCostBasis("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add position");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add Positions</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleAdd} className="space-y-3">
          {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="symbol">Ticker</Label>
              <Input id="symbol" value={symbol} onChange={(e) => setSymbol(e.target.value)} placeholder="AAPL" required />
            </div>
            <div className="space-y-1">
              <Label htmlFor="name">Name (optional)</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Apple Inc." />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label htmlFor="qty">Shares</Label>
              <Input id="qty" type="number" step="any" value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
            </div>
            <div className="space-y-1">
              <Label htmlFor="cost">Cost/Share (optional)</Label>
              <Input id="cost" type="number" step="any" value={costBasis} onChange={(e) => setCostBasis(e.target.value)} />
            </div>
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Adding..." : "Add Position"}
          </Button>
        </form>

        {positions.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="text-sm font-medium text-neutral-500">{positions.length} position(s) added</div>
            <div className="space-y-1">
              {positions.map((p) => (
                <div key={p.id} className="flex justify-between text-sm rounded bg-neutral-50 px-3 py-2">
                  <span className="font-medium">{p.symbol}</span>
                  <span className="text-neutral-500">{p.quantity} shares</span>
                </div>
              ))}
            </div>
            <Button onClick={onDone} className="w-full mt-3">
              Done — Go to Dashboard
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
