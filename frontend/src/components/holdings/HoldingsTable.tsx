"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/utils";
import { Search, ArrowUpDown } from "lucide-react";

interface Holding {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
  market_value: number;
  weight: number;
  unrealized_pnl: number | null;
  sector: string | null;
  country: string | null;
}

interface Props {
  holdings: Holding[];
  onSelect?: (symbol: string) => void;
}

type SortKey = "symbol" | "weight" | "market_value" | "unrealized_pnl";

export function HoldingsTable({ holdings, onSelect }: Props) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("weight");
  const [sortAsc, setSortAsc] = useState(false);

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  }

  const filtered = holdings
    .filter((h) =>
      h.symbol.toLowerCase().includes(search.toLowerCase()) ||
      h.name.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (typeof av === "string") return sortAsc ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
      return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
        <Input
          placeholder="Search holdings..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>
      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-neutral-50">
              <th className="px-4 py-3 text-left font-medium cursor-pointer" onClick={() => handleSort("symbol")}>
                <span className="flex items-center gap-1">Symbol <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-left font-medium">Name</th>
              <th className="px-4 py-3 text-right font-medium">Qty</th>
              <th className="px-4 py-3 text-right font-medium">Price</th>
              <th className="px-4 py-3 text-right font-medium cursor-pointer" onClick={() => handleSort("market_value")}>
                <span className="flex items-center justify-end gap-1">Value <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-right font-medium cursor-pointer" onClick={() => handleSort("weight")}>
                <span className="flex items-center justify-end gap-1">Weight <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-right font-medium cursor-pointer" onClick={() => handleSort("unrealized_pnl")}>
                <span className="flex items-center justify-end gap-1">P&L <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-left font-medium">Sector</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((h) => (
              <tr
                key={h.symbol}
                className="border-b last:border-0 hover:bg-neutral-50 cursor-pointer transition-colors"
                onClick={() => onSelect?.(h.symbol)}
              >
                <td className="px-4 py-3 font-medium">{h.symbol}</td>
                <td className="px-4 py-3 text-neutral-600 truncate max-w-[150px]">{h.name}</td>
                <td className="px-4 py-3 text-right">{h.quantity.toLocaleString()}</td>
                <td className="px-4 py-3 text-right">{formatCurrency(h.price)}</td>
                <td className="px-4 py-3 text-right font-medium">{formatCurrency(h.market_value)}</td>
                <td className="px-4 py-3 text-right">
                  <Badge variant={h.weight > 15 ? "destructive" : h.weight > 10 ? "warning" : "secondary"}>
                    {h.weight.toFixed(1)}%
                  </Badge>
                </td>
                <td className={`px-4 py-3 text-right ${h.unrealized_pnl && h.unrealized_pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                  {h.unrealized_pnl !== null ? formatCurrency(h.unrealized_pnl) : "—"}
                </td>
                <td className="px-4 py-3 text-neutral-500 text-xs">{h.sector || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
