"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, MessageSquare } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export function WealthAiSummary() {
  const [summary, setSummary] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    setLoading(true);
    try {
      const res = await api.post<{ summary: string }>("/ai/summary");
      setSummary(res.summary);
    } catch {
      setSummary("Unable to generate summary at this time.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">AI Summary</CardTitle>
          <div className="flex items-center gap-2">
            {!summary && (
              <Button variant="outline" size="sm" onClick={handleGenerate} disabled={loading}>
                <Sparkles className="h-3 w-3 mr-1" />
                {loading ? "Generating..." : "Generate"}
              </Button>
            )}
            <Link
              href="/chat"
              className="flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-900 transition-colors"
            >
              <MessageSquare className="h-3 w-3" />
              Ask AI
            </Link>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {summary ? (
          <div className="space-y-2">
            <p className="text-sm text-neutral-700 leading-relaxed">{summary}</p>
            <Button variant="ghost" size="sm" onClick={handleGenerate} disabled={loading} className="text-xs">
              {loading ? "Regenerating..." : "Regenerate"}
            </Button>
          </div>
        ) : (
          <p className="text-sm text-neutral-400 italic">
            Click Generate to get an AI-powered summary of your wealth profile.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
