"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AddPositionForm } from "@/components/portfolio/AddPositionForm";
import { CsvUploadWizard } from "@/components/portfolio/CsvUploadWizard";
import type { Portfolio } from "@/types";

type Step = "name" | "method" | "manual" | "csv";

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>("name");
  const [portfolioName, setPortfolioName] = useState("My Portfolio");
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    router.replace("/login");
    return null;
  }

  async function handleCreatePortfolio(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const p = await api.post<Portfolio>("/portfolios", { name: portfolioName });
      setPortfolio(p);
      setStep("method");
    } finally {
      setLoading(false);
    }
  }

  function handleDone() {
    if (portfolio) {
      router.push("/overview");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4 py-12">
      <div className="w-full max-w-lg space-y-6">
        {step === "name" && (
          <Card>
            <CardHeader>
              <CardTitle>Create Your Portfolio</CardTitle>
              <CardDescription>Give your portfolio a name to get started</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreatePortfolio} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Portfolio Name</Label>
                  <Input id="name" value={portfolioName} onChange={(e) => setPortfolioName(e.target.value)} required />
                </div>
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Creating..." : "Continue"}
                </Button>
              </form>
            </CardContent>
          </Card>
        )}

        {step === "method" && (
          <Card>
            <CardHeader>
              <CardTitle>Add Your Holdings</CardTitle>
              <CardDescription>Choose how you want to add your positions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("manual")}>
                <div className="text-left">
                  <div className="font-medium">Add Manually</div>
                  <div className="text-sm text-neutral-500">Enter positions one at a time</div>
                </div>
              </Button>
              <Button variant="outline" className="w-full justify-start h-auto py-4 px-4" onClick={() => setStep("csv")}>
                <div className="text-left">
                  <div className="font-medium">Upload CSV</div>
                  <div className="text-sm text-neutral-500">Import from a spreadsheet export</div>
                </div>
              </Button>
            </CardContent>
          </Card>
        )}

        {step === "manual" && portfolio && (
          <div className="space-y-4">
            <AddPositionForm portfolioId={portfolio.id} onDone={handleDone} />
            <Button variant="ghost" className="w-full" onClick={() => setStep("method")}>
              Back
            </Button>
          </div>
        )}

        {step === "csv" && portfolio && (
          <div className="space-y-4">
            <CsvUploadWizard portfolioId={portfolio.id} onDone={handleDone} />
            <Button variant="ghost" className="w-full" onClick={() => setStep("method")}>
              Back
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
