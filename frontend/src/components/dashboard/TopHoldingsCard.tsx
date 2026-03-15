"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { formatCurrency } from "@/lib/utils";

interface Holding {
  symbol: string;
  name: string;
  weight: number;
  market_value: number;
}

interface Props {
  holdings: Holding[];
}

export function TopHoldingsCard({ holdings }: Props) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">Top Holdings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {holdings.slice(0, 5).map((h) => (
            <div key={h.symbol} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-md bg-neutral-100 flex items-center justify-center text-xs font-bold text-neutral-700">
                  {h.symbol.slice(0, 2)}
                </div>
                <div>
                  <div className="text-sm font-medium">{h.symbol}</div>
                  <div className="text-xs text-neutral-500 truncate max-w-[120px]">{h.name}</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm font-medium">{h.weight.toFixed(1)}%</div>
                <div className="text-xs text-neutral-500">{formatCurrency(h.market_value)}</div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
