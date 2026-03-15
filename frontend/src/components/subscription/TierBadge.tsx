"use client";

import { useSubscription } from "@/hooks/use-subscription";

const TIER_STYLES: Record<string, string> = {
  free: "bg-slate-700 text-slate-300",
  pro: "bg-indigo-600/20 text-indigo-400",
  family: "bg-purple-600/20 text-purple-400",
};

const TIER_LABELS: Record<string, string> = {
  free: "Free",
  pro: "Pro",
  family: "Family",
};

export function TierBadge() {
  const { data } = useSubscription();
  const tier = data?.tier || "free";

  return (
    <span className={`text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 rounded-full ${TIER_STYLES[tier] || TIER_STYLES.free}`}>
      {TIER_LABELS[tier] || "Free"}
    </span>
  );
}
