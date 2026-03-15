"use client";

import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { UpgradePrompt } from "@/components/subscription/UpgradePrompt";
import { useSubscription } from "@/hooks/use-subscription";
import { api } from "@/lib/api";
import {
  FileText,
  Receipt,
  Download,
  Loader2,
  BarChart3,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://tradeiq-production-84c6.up.railway.app";

async function downloadReport(path: string, filename: string) {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) throw new Error("Failed to download report");

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

interface ReportCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}

function ReportCard({ title, description, icon, children }: ReportCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default function ReportsPage() {
  const { data: subscription } = useSubscription();
  const tier = subscription?.tier || "free";

  const [monthlyMonth, setMonthlyMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });
  const [taxYear, setTaxYear] = useState(() => String(new Date().getFullYear() - 1));
  const [downloading, setDownloading] = useState<string | null>(null);

  async function handleDownload(id: string, path: string, filename: string) {
    setDownloading(id);
    try {
      await downloadReport(path, filename);
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setDownloading(null);
    }
  }

  if (tier === "free") {
    return (
      <AppShell>
        <div className="max-w-2xl space-y-6">
          <div>
            <h2 className="text-2xl font-bold">Reports</h2>
            <p className="text-sm text-neutral-500">
              Download detailed financial reports and summaries
            </p>
          </div>
          <UpgradePrompt feature="Financial Reports" />
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="max-w-2xl space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Reports</h2>
          <p className="text-sm text-neutral-500">
            Download detailed financial reports and summaries
          </p>
        </div>

        {/* Monthly Report */}
        <ReportCard
          title="Monthly Report"
          description="Overview of your net worth, asset changes, and transactions for a given month"
          icon={<FileText className="h-4 w-4" />}
        >
          <div className="space-y-4">
            <div>
              <Label>Month</Label>
              <Input
                type="month"
                value={monthlyMonth}
                onChange={(e) => setMonthlyMonth(e.target.value)}
                className="mt-1"
              />
            </div>
            <Button
              onClick={() =>
                handleDownload(
                  "monthly",
                  `/reports/monthly?month=${monthlyMonth}`,
                  `monthly-report-${monthlyMonth}.pdf`
                )
              }
              disabled={downloading === "monthly"}
              className="w-full"
            >
              {downloading === "monthly" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Download Monthly Report
                </>
              )}
            </Button>
          </div>
        </ReportCard>

        {/* Tax Summary */}
        <ReportCard
          title="Tax Summary"
          description="Capital gains, dividends, and interest income for your tax return"
          icon={<Receipt className="h-4 w-4" />}
        >
          <div className="space-y-4">
            <div>
              <Label>Tax Year</Label>
              <select
                className="w-full rounded-md border border-neutral-200 px-3 py-2 text-sm mt-1"
                value={taxYear}
                onChange={(e) => setTaxYear(e.target.value)}
              >
                {Array.from({ length: 5 }, (_, i) => {
                  const y = new Date().getFullYear() - i;
                  return (
                    <option key={y} value={String(y)}>
                      {y}/{y + 1}
                    </option>
                  );
                })}
              </select>
            </div>
            <Button
              onClick={() =>
                handleDownload(
                  "tax",
                  `/reports/tax?year=${taxYear}`,
                  `tax-summary-${taxYear}.pdf`
                )
              }
              disabled={downloading === "tax"}
              className="w-full"
            >
              {downloading === "tax" ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Download Tax Summary
                </>
              )}
            </Button>
          </div>
        </ReportCard>

        {/* Net Worth Export */}
        <ReportCard
          title="Net Worth Export"
          description="Export your complete net worth history as a CSV spreadsheet"
          icon={<BarChart3 className="h-4 w-4" />}
        >
          <Button
            onClick={() =>
              handleDownload(
                "export",
                "/reports/net-worth-export",
                `net-worth-export-${new Date().toISOString().split("T")[0]}.csv`
              )
            }
            disabled={downloading === "export"}
            className="w-full"
          >
            {downloading === "export" ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4 mr-2" />
                Download CSV Export
              </>
            )}
          </Button>
        </ReportCard>
      </div>
    </AppShell>
  );
}
