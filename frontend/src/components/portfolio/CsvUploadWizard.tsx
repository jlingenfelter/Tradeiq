"use client";

import { useState, useRef } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface Props {
  portfolioId: string;
  onDone: () => void;
}

interface UploadResult {
  preview: Record<string, string>[];
  columns: string[];
  row_count: number;
  upload_id: string;
}

interface ImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

export function CsvUploadWizard({ portfolioId, onDone }: Props) {
  const [step, setStep] = useState<"upload" | "preview" | "done">("upload");
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const FIELD_OPTIONS = [
    { value: "", label: "— Skip —" },
    { value: "symbol", label: "Symbol / Ticker" },
    { value: "quantity", label: "Quantity / Shares" },
    { value: "asset_name", label: "Company Name" },
    { value: "cost_basis_per_share", label: "Cost per Share" },
    { value: "cost_basis_total", label: "Total Cost Basis" },
    { value: "currency", label: "Currency" },
  ];

  async function handleUpload() {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setError("");
    setLoading(true);
    try {
      const result = await api.upload<UploadResult>(`/portfolios/${portfolioId}/import/csv`, file);
      setUploadResult(result);
      // Try to auto-detect mapping
      const autoMap: Record<string, string> = {};
      for (const col of result.columns) {
        const lower = col.toLowerCase().trim();
        if (["symbol", "ticker", "stock"].includes(lower)) autoMap[col] = "symbol";
        else if (["quantity", "shares", "qty"].includes(lower)) autoMap[col] = "quantity";
        else if (["name", "company", "company_name"].includes(lower)) autoMap[col] = "asset_name";
        else if (["avg_cost", "cost_basis", "cost_per_share"].includes(lower)) autoMap[col] = "cost_basis_per_share";
      }
      setColumnMapping(autoMap);
      setStep("preview");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleConfirm() {
    if (!uploadResult) return;
    setError("");
    setLoading(true);
    try {
      const result = await api.post<ImportResult>(`/portfolios/${portfolioId}/import/csv/confirm`, {
        upload_id: uploadResult.upload_id,
        column_mapping: columnMapping,
        account_name: "CSV Import",
      });
      setImportResult(result);
      setStep("done");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Import failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Import CSV</CardTitle>
        <CardDescription>Upload a CSV file with your portfolio holdings</CardDescription>
      </CardHeader>
      <CardContent>
        {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 mb-4">{error}</div>}

        {step === "upload" && (
          <div className="space-y-4">
            <div className="border-2 border-dashed border-neutral-200 rounded-lg p-8 text-center">
              <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleUpload} />
              <p className="text-sm text-neutral-500 mb-3">Select a CSV file with your holdings</p>
              <Button variant="outline" onClick={() => fileRef.current?.click()} disabled={loading}>
                {loading ? "Uploading..." : "Choose File"}
              </Button>
            </div>
          </div>
        )}

        {step === "preview" && uploadResult && (
          <div className="space-y-4">
            <p className="text-sm text-neutral-500">{uploadResult.row_count} rows found. Map your columns:</p>
            <div className="space-y-2">
              {uploadResult.columns.map((col) => (
                <div key={col} className="flex items-center gap-3">
                  <span className="text-sm font-mono w-40 truncate">{col}</span>
                  <select
                    className="flex-1 rounded-md border border-neutral-200 px-2 py-1.5 text-sm"
                    value={columnMapping[col] || ""}
                    onChange={(e) => setColumnMapping({ ...columnMapping, [col]: e.target.value })}
                  >
                    {FIELD_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {/* Preview table */}
            <div className="overflow-x-auto border rounded-md">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-neutral-50">
                    {uploadResult.columns.map((col) => (
                      <th key={col} className="px-2 py-1 text-left font-medium">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {uploadResult.preview.slice(0, 5).map((row, i) => (
                    <tr key={i} className="border-t">
                      {uploadResult.columns.map((col) => (
                        <td key={col} className="px-2 py-1">{row[col]}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <Button onClick={handleConfirm} className="w-full" disabled={loading}>
              {loading ? "Importing..." : `Import ${uploadResult.row_count} positions`}
            </Button>
          </div>
        )}

        {step === "done" && importResult && (
          <div className="space-y-4 text-center">
            <div className="text-lg font-medium">Import Complete</div>
            <div className="text-sm text-neutral-500">
              {importResult.imported} positions imported, {importResult.skipped} skipped
            </div>
            {importResult.errors.length > 0 && (
              <div className="text-sm text-red-600">
                {importResult.errors.map((e, i) => <div key={i}>{e}</div>)}
              </div>
            )}
            <Button onClick={onDone} className="w-full">
              Go to Dashboard
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
