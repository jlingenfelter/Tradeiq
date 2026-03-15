"use client";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { MessageSquare } from "lucide-react";
import Link from "next/link";

interface Props {
  summary: string | null;
  portfolioId: string;
}

export function AiSummaryPanel({ summary, portfolioId }: Props) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">AI Summary</CardTitle>
          <Link
            href="/chat"
            className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-900 transition-colors"
          >
            <MessageSquare className="h-3 w-3" />
            Ask AI
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {summary ? (
          <p className="text-sm text-neutral-700 leading-relaxed">{summary}</p>
        ) : (
          <p className="text-sm text-neutral-400 italic">
            AI summary will appear once analytics are computed.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
