"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Wallet, CreditCard, PieChart,
  TrendingUp, AlertTriangle, MessageSquare, Settings,
  LogOut, Briefcase, Link2, Target, Bell, Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

const navigation = [
  { name: "Overview", href: "/overview", icon: LayoutDashboard },
  { name: "Assets", href: "/assets", icon: Wallet },
  { name: "Liabilities", href: "/liabilities", icon: CreditCard },
  { name: "Portfolio", href: "/dashboard", icon: Briefcase },
  { name: "Allocation & Risk", href: "/allocation", icon: PieChart },
  { name: "Goals", href: "/goals", icon: Target },
  { name: "Insights", href: "/insights", icon: Sparkles },
  { name: "Alerts", href: "/alerts", icon: Bell },
  { name: "History", href: "/history", icon: TrendingUp },
  { name: "Warnings", href: "/warnings", icon: AlertTriangle },
  { name: "Connect", href: "/connect", icon: Link2 },
  { name: "Ask AI", href: "/chat", icon: MessageSquare },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside className="flex h-screen w-60 flex-col bg-slate-900">
      <div className="flex h-14 items-center px-5">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <span className="text-white text-xs font-bold">W</span>
          </div>
          <h1 className="text-base font-semibold tracking-tight text-white">Wealth Copilot</h1>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 px-3 pt-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",
                isActive
                  ? "bg-indigo-600/20 text-indigo-400"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              )}
            >
              <item.icon className={cn("h-4 w-4", isActive && "text-indigo-400")} />
              {item.name}
              {isActive && (
                <div className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-400" />
              )}
            </Link>
          );
        })}
      </nav>
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
