"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Wallet, CreditCard, PieChart,
  TrendingUp, AlertTriangle, MessageSquare, Settings,
  LogOut, Briefcase,
} from "lucide-react";
import { useAuth } from "@/lib/auth";

const navigation = [
  { name: "Overview", href: "/overview", icon: LayoutDashboard },
  { name: "Assets", href: "/assets", icon: Wallet },
  { name: "Liabilities", href: "/liabilities", icon: CreditCard },
  { name: "Portfolio", href: "/dashboard", icon: Briefcase },
  { name: "Allocation & Risk", href: "/allocation", icon: PieChart },
  { name: "History", href: "/history", icon: TrendingUp },
  { name: "Warnings", href: "/warnings", icon: AlertTriangle },
  { name: "Ask AI", href: "/chat", icon: MessageSquare },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside className="flex h-screen w-60 flex-col border-r border-neutral-200 bg-white">
      <div className="flex h-14 items-center border-b border-neutral-200 px-4">
        <h1 className="text-lg font-semibold tracking-tight">Wealth Copilot</h1>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-neutral-100 text-neutral-900"
                  : "text-neutral-500 hover:bg-neutral-50 hover:text-neutral-900"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-neutral-200 p-3">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-neutral-500 hover:bg-neutral-50 hover:text-neutral-900 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
