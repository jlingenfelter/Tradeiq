"use client";

import Link from "next/link";
import { Lock } from "lucide-react";

interface UpgradePromptProps {
  feature: string;
  tier?: "pro" | "family";
  compact?: boolean;
}

export function UpgradePrompt({ feature, tier = "pro", compact = false }: UpgradePromptProps) {
  if (compact) {
    return (
      <Link
        href="/pricing"
        className="inline-flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-700 font-medium"
      >
        <Lock className="h-3 w-3" />
        Upgrade to {tier === "family" ? "Family" : "Pro"}
      </Link>
    );
  }

  return (
    <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-4">
      <div className="flex items-start gap-3">
        <div className="h-8 w-8 rounded-full bg-indigo-100 flex items-center justify-center shrink-0">
          <Lock className="h-4 w-4 text-indigo-600" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-indigo-900">
            Upgrade to unlock {feature}
          </p>
          <p className="text-xs text-indigo-600 mt-0.5">
            This feature is available on the {tier === "family" ? "Family" : "Pro"} plan.
          </p>
          <Link
            href="/pricing"
            className="inline-flex items-center mt-2 px-3 py-1.5 text-xs font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors"
          >
            View Plans
          </Link>
        </div>
      </div>
    </div>
  );
}
