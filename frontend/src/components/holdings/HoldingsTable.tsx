"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/utils";
import { Search, ArrowUpDown, TrendingUp, TrendingDown } from "lucide-react";
import Image from "next/image";

interface Holding {
  symbol: string;
  name: string;
  quantity: number;
  price: number;
  previous_close?: number | null;
  market_value: number;
  weight: number;
  unrealized_pnl: number | null;
  sector: string | null;
  country?: string | null;
  asset_type?: string;
}

interface Props {
  holdings: Holding[];
  onSelect?: (symbol: string) => void;
}

type SortKey = "symbol" | "weight" | "market_value" | "unrealized_pnl" | "day_change";

// Known crypto symbols for icon display and formatting
const CRYPTO_SYMBOLS = new Set([
  "BTC", "ETH", "USDT", "USDC", "BNB", "XRP", "ADA", "DOGE", "SOL", "DOT",
  "MATIC", "POL", "AVAX", "LINK", "UNI", "AAVE", "ATOM", "LTC", "FIL", "NEAR",
  "ARB", "OP", "APT", "SUI", "SEI", "INJ", "TIA", "RENDER", "RNDR", "FET",
  "GRT", "IMX", "MKR", "SNX", "CRV", "LDO", "RPL", "COMP", "SUSHI", "BAL",
  "1INCH", "ENS", "PEPE", "SHIB", "WIF", "BONK", "FLOKI", "DAI", "WBTC",
  "WETH", "STETH", "WSTETH", "RETH", "CBETH", "EIGEN", "ENA", "ETHFI",
  "PENDLE", "BLUR", "TON", "TRX", "BCH", "XMR", "HBAR", "ICP", "ALGO",
]);

function isCrypto(holding: Holding): boolean {
  return holding.asset_type === "crypto" || CRYPTO_SYMBOLS.has(holding.symbol.toUpperCase());
}

function getCryptoIconUrl(symbol: string): string {
  // Use CoinGecko's free icon CDN via cryptoicons or a reliable CDN
  const sym = symbol.toLowerCase();
  return `https://assets.coingecko.com/coins/images/1/small/bitcoin.png`;
}

function formatQuantity(qty: number, isCryptoAsset: boolean): string {
  if (!isCryptoAsset) return qty.toLocaleString();
  // For crypto, show more decimal places for small quantities
  if (qty >= 1000) return qty.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (qty >= 1) return qty.toLocaleString(undefined, { maximumFractionDigits: 4 });
  if (qty >= 0.001) return qty.toLocaleString(undefined, { maximumFractionDigits: 6 });
  return qty.toLocaleString(undefined, { maximumFractionDigits: 8 });
}

function getDayChange(holding: Holding): { pct: number; value: number } | null {
  if (!holding.previous_close || holding.previous_close === 0) return null;
  const pct = ((holding.price - holding.previous_close) / holding.previous_close) * 100;
  const value = (holding.price - holding.previous_close) * holding.quantity;
  return { pct, value };
}

export function HoldingsTable({ holdings, onSelect }: Props) {
  const [search, setSearch] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("weight");
  const [sortAsc, setSortAsc] = useState(false);
  const [filter, setFilter] = useState<"all" | "crypto" | "stocks">("all");

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  }

  const filtered = holdings
    .filter((h) => {
      if (filter === "crypto" && !isCrypto(h)) return false;
      if (filter === "stocks" && isCrypto(h)) return false;
      return (
        h.symbol.toLowerCase().includes(search.toLowerCase()) ||
        h.name.toLowerCase().includes(search.toLowerCase())
      );
    })
    .sort((a, b) => {
      if (sortKey === "day_change") {
        const aChange = getDayChange(a)?.pct ?? 0;
        const bChange = getDayChange(b)?.pct ?? 0;
        return sortAsc ? aChange - bChange : bChange - aChange;
      }
      const av = a[sortKey as keyof Holding] ?? 0;
      const bv = b[sortKey as keyof Holding] ?? 0;
      if (typeof av === "string") return sortAsc ? av.localeCompare(bv as string) : (bv as string).localeCompare(av);
      return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });

  const cryptoCount = holdings.filter(isCrypto).length;
  const stockCount = holdings.length - cryptoCount;
  const totalCryptoValue = holdings.filter(isCrypto).reduce((sum, h) => sum + h.market_value, 0);

  return (
    <div className="space-y-3">
      {/* Search + filter bar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <Input
            placeholder="Search holdings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <div className="flex rounded-lg border border-neutral-200 overflow-hidden text-sm">
          <button
            className={`px-3 py-2 transition-colors ${filter === "all" ? "bg-neutral-900 text-white" : "bg-white text-neutral-600 hover:bg-neutral-50"}`}
            onClick={() => setFilter("all")}
          >
            All ({holdings.length})
          </button>
          {cryptoCount > 0 && (
            <button
              className={`px-3 py-2 border-l transition-colors ${filter === "crypto" ? "bg-neutral-900 text-white" : "bg-white text-neutral-600 hover:bg-neutral-50"}`}
              onClick={() => setFilter("crypto")}
            >
              Crypto ({cryptoCount})
            </button>
          )}
          {stockCount > 0 && (
            <button
              className={`px-3 py-2 border-l transition-colors ${filter === "stocks" ? "bg-neutral-900 text-white" : "bg-white text-neutral-600 hover:bg-neutral-50"}`}
              onClick={() => setFilter("stocks")}
            >
              Stocks ({stockCount})
            </button>
          )}
        </div>
      </div>

      {/* Crypto summary banner */}
      {filter === "crypto" && cryptoCount > 0 && (
        <div className="flex items-center gap-4 rounded-lg bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 px-4 py-3">
          <div className="text-2xl">₿</div>
          <div>
            <div className="text-sm text-neutral-500">Total Crypto Holdings</div>
            <div className="text-lg font-bold">{formatCurrency(totalCryptoValue)}</div>
          </div>
          <div className="ml-auto text-sm text-neutral-500">
            {cryptoCount} asset{cryptoCount !== 1 ? "s" : ""}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-neutral-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-neutral-50">
              <th className="px-4 py-3 text-left font-medium cursor-pointer" onClick={() => handleSort("symbol")}>
                <span className="flex items-center gap-1">Asset <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-right font-medium">Qty</th>
              <th className="px-4 py-3 text-right font-medium">Price</th>
              <th className="px-4 py-3 text-right font-medium cursor-pointer" onClick={() => handleSort("day_change")}>
                <span className="flex items-center justify-end gap-1">24h <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-right font-medium cursor-pointer" onClick={() => handleSort("market_value")}>
                <span className="flex items-center justify-end gap-1">Value <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-right font-medium cursor-pointer" onClick={() => handleSort("weight")}>
                <span className="flex items-center justify-end gap-1">Weight <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-right font-medium cursor-pointer" onClick={() => handleSort("unrealized_pnl")}>
                <span className="flex items-center justify-end gap-1">P&L <ArrowUpDown className="h-3 w-3" /></span>
              </th>
              <th className="px-4 py-3 text-left font-medium">Type</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((h) => {
              const crypto = isCrypto(h);
              const dayChange = getDayChange(h);
              return (
                <tr
                  key={h.symbol}
                  className="border-b last:border-0 hover:bg-neutral-50 cursor-pointer transition-colors"
                  onClick={() => onSelect?.(h.symbol)}
                >
                  {/* Symbol + Name column */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      {crypto ? (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-amber-500 text-white text-xs font-bold shrink-0">
                          {h.symbol.slice(0, 2)}
                        </div>
                      ) : (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-neutral-100 text-neutral-600 text-xs font-bold shrink-0">
                          {h.symbol.slice(0, 2)}
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="font-medium">{h.symbol}</div>
                        <div className="text-xs text-neutral-500 truncate max-w-[120px]">{h.name}</div>
                      </div>
                    </div>
                  </td>
                  {/* Quantity */}
                  <td className="px-4 py-3 text-right font-mono text-xs">
                    {formatQuantity(h.quantity, crypto)}
                  </td>
                  {/* Price */}
                  <td className="px-4 py-3 text-right">
                    {h.price >= 1 ? formatCurrency(h.price) : `$${h.price.toFixed(6)}`}
                  </td>
                  {/* 24h Change */}
                  <td className="px-4 py-3 text-right">
                    {dayChange ? (
                      <div className={`flex items-center justify-end gap-1 ${dayChange.pct >= 0 ? "text-green-600" : "text-red-600"}`}>
                        {dayChange.pct >= 0 ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : (
                          <TrendingDown className="h-3 w-3" />
                        )}
                        <span className="text-xs font-medium">
                          {dayChange.pct >= 0 ? "+" : ""}{dayChange.pct.toFixed(2)}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-neutral-400">—</span>
                    )}
                  </td>
                  {/* Market Value */}
                  <td className="px-4 py-3 text-right font-medium">{formatCurrency(h.market_value)}</td>
                  {/* Weight */}
                  <td className="px-4 py-3 text-right">
                    <Badge variant={h.weight > 15 ? "destructive" : h.weight > 10 ? "warning" : "secondary"}>
                      {h.weight.toFixed(1)}%
                    </Badge>
                  </td>
                  {/* P&L */}
                  <td className={`px-4 py-3 text-right ${h.unrealized_pnl && h.unrealized_pnl >= 0 ? "text-green-600" : "text-red-600"}`}>
                    {h.unrealized_pnl !== null ? formatCurrency(h.unrealized_pnl) : "—"}
                  </td>
                  {/* Type badge */}
                  <td className="px-4 py-3">
                    {crypto ? (
                      <Badge className="bg-orange-100 text-orange-700 hover:bg-orange-100 border-0 text-xs">
                        Crypto
                      </Badge>
                    ) : (
                      <Badge variant="secondary" className="text-xs">
                        {h.sector || "Equity"}
                      </Badge>
                    )}
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-neutral-500">
                  No holdings found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
