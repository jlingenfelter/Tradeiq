"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Wallet, CreditCard, PieChart,
  TrendingUp, AlertTriangle, MessageSquare, Settings,
  LogOut, Briefcase, Link2, Target, Bell, Sparkles,
  Calculator, FileText, Users, Crown,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { TierBadge } from "@/components/subscription/TierBadge";
import { useSubscription } from "@/hooks/use-subscription";

const navigation = [
  { name: "Overview", href: "/overview", icon: LayoutDashboard },
  { name: "Assets", href: "/assets", icon: Wallet },
  { name: "Liabilities", href: "/liabilities", icon: CreditCard },
  { name: "Portfolio", href: "/dashboard", icon: Briefcase },
  { name: "Allocation & Risk", href: "/allocation", icon: PieChart },
  { name: "Goals", href: "/goals", icon: Target },
  { name: "Insights", href: "/insights", icon: Sparkles },
  { name: "Alerts", href: "/alerts", icon: Bell },
  { name: "Scenarios", href: "/scenarios", icon: Calculator, pro: true },
  { name: "Reports", href: "/reports", icon: FileText, pro: true },
  { name: "Household", href: "/household", icon: Users, family: true },
  { name: "History", href: "/history", icon: TrendingUp },
  { name: "Warnings", href: "/warnings", icon: AlertTriangle },
  { name: "Connect", href: "/connect", icon: Link2 },
  { name: "Ask AI", href: "/chat", icon: MessageSquare },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();
  const { data: subscription } = useSubscription();
  const tier = subscription?.tier || "free";

  return (
    <aside className="flex h-screen w-60 flex-col bg-slate-900">
      <div className="flex h-14 items-center px-5">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <span className="text-white text-xs font-bold">W</span>
          </div>
          <h1 className="text-base font-semibold tracking-tight text-white">Wealth Copilot</h1>
          <TierBadge />
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 px-3 pt-4 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const isPro = "pro" in item && item.pro;
          const isFamily = "family" in item && item.family;
          const locked = (isPro && tier === "free") || (isFamily && tier !== "family");

          return (
            <Link
              key={item.name}
              href={locked ? "/pricing" : item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",
                isActive
                  ? "bg-indigo-600/20 text-indigo-400"
                  : locked
                    ? "text-slate-600 hover:bg-slate-800/50 hover:text-slate-500"
                    : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              )}
            >
              <item.icon className={cn("h-4 w-4", isActive && "text-indigo-400")} />
              {item.name}
              {locked && (
                <span className="ml-auto text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">
                  {isFamily ? "Family" : "Pro"}
                </span>
              )}
              {isActive && !locked && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-400" />
              )}
            </Link>
          );
        })}
      </nav>

      {tier === "free" && (
        <div className="px-3 py-2">
          <Link
            href="/pricing"
            className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium bg-gradient-to-r from-indigo-600/20 to-purple-600/20 text-indigo-400 hover:from-indigo-600/30 hover:to-purple-600/30 transition-colors"
          >
            <Crown className="h-4 w-4" />
            Upgrade Plan
          </Link>
        </div>
      )}

      <div className="border-t border-slate-800 px-3 py-3">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
