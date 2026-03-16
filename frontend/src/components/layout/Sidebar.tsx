"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Wallet, CreditCard, PieChart,
  TrendingUp, AlertTriangle, MessageSquare, Settings,
  LogOut, Briefcase, Link2, Target, Bell, Sparkles,
  Calculator, FileText, Users, Crown, Menu, X,
} from "lucide-react";
import { useAuth } from "@/lib/auth";
import { TierBadge } from "@/components/subscription/TierBadge";
import { useSubscription } from "@/hooks/use-subscription";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useState, useEffect, useCallback } from "react";

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

  const [mobileOpen, setMobileOpen] = useState(false);
  const [tabletExpanded, setTabletExpanded] = useState(false);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  // Prevent body scroll when mobile sidebar is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  const sidebarContent = (opts: { collapsed?: boolean; onNavClick?: () => void }) => {
    const { collapsed = false, onNavClick } = opts;
    return (
      <>
        {/* Logo header */}
        <div className="flex h-16 items-center px-5 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="logo-shine h-8 w-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 overflow-hidden">
              <span className="text-white text-sm font-bold">T</span>
            </div>
            {!collapsed && (
              <>
                <h1 className="text-base font-semibold tracking-tight text-white whitespace-nowrap">TradeIQ</h1>
                <TierBadge />
              </>
            )}
          </div>
          {/* Close button on mobile */}
          {onNavClick && (
            <button
              onClick={onNavClick}
              className="ml-auto p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 md:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Gradient separator */}
        <div className="mx-4 h-px bg-gradient-to-r from-transparent via-slate-700 to-transparent shrink-0" />

        {/* Navigation */}
        <nav className="flex-1 space-y-0.5 px-3 pt-3 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const isPro = "pro" in item && item.pro;
            const isFamily = "family" in item && item.family;
            const locked = (isPro && tier === "free") || (isFamily && tier !== "family");

            return (
              <Link
                key={item.name}
                href={locked ? "/pricing" : item.href}
                onClick={onNavClick}
                title={collapsed ? item.name : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium relative",
                  collapsed && "justify-center px-2",
                  isActive
                    ? "bg-indigo-600/20 text-indigo-400 before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:h-5 before:w-[2px] before:rounded-r before:bg-indigo-400"
                    : locked
                      ? "text-slate-600 hover:bg-slate-800/50 hover:text-slate-500"
                      : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                )}
              >
                <item.icon className={cn("h-4 w-4 shrink-0", isActive && "text-indigo-400")} />
                {!collapsed && (
                  <>
                    {item.name}
                    {locked && (
                      <span className="ml-auto text-[9px] uppercase tracking-wider font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">
                        {isFamily ? "Family" : "Pro"}
                      </span>
                    )}
                    {isActive && !locked && (
                      <div className="ml-auto h-1.5 w-1.5 rounded-full bg-indigo-400" />
                    )}
                  </>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Upgrade CTA */}
        {tier === "free" && !collapsed && (
          <div className="px-3 py-2 shrink-0">
            <Link
              href="/pricing"
              onClick={onNavClick}
              className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium bg-gradient-to-r from-indigo-600/20 to-purple-600/20 text-indigo-400 hover:from-indigo-600/30 hover:to-purple-600/30 transition-colors"
            >
              <Crown className="h-4 w-4" />
              Upgrade Plan
            </Link>
          </div>
        )}

        {/* Theme toggle */}
        {!collapsed && (
          <div className="px-3 shrink-0">
            <ThemeToggle />
          </div>
        )}

        {/* Sign out */}
        <div className="border-t border-slate-800 px-3 py-3 shrink-0">
          <button
            onClick={() => {
              onNavClick?.();
              logout();
            }}
            className={cn(
              "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200",
              collapsed && "justify-center px-2"
            )}
            title={collapsed ? "Sign out" : undefined}
          >
            <LogOut className="h-4 w-4 shrink-0" />
            {!collapsed && "Sign out"}
          </button>
        </div>
      </>
    );
  };

  return (
    <>
      {/* ==================== Mobile header bar ==================== */}
      <div className="fixed top-0 left-0 right-0 z-40 flex h-14 items-center justify-between bg-slate-900 px-4 md:hidden">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <span className="text-base font-semibold text-white">TradeIQ</span>
        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <span className="text-white text-xs font-bold">U</span>
        </div>
      </div>

      {/* ==================== Mobile sidebar overlay ==================== */}
      {/* Backdrop */}
      <div
        className={cn(
          "fixed inset-0 z-50 bg-black/50 transition-opacity duration-300 md:hidden",
          mobileOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={closeMobile}
        aria-hidden="true"
      />
      {/* Sliding sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 z-50 flex h-screen w-72 flex-col bg-slate-900 transition-transform duration-300 ease-in-out md:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebarContent({ onNavClick: closeMobile })}
      </aside>

      {/* ==================== Tablet sidebar (768-1024) ==================== */}
      <aside
        className={cn(
          "hidden md:flex lg:hidden h-screen flex-col bg-slate-900 transition-all duration-200 ease-in-out shrink-0",
          tabletExpanded ? "w-60" : "w-16"
        )}
        onMouseEnter={() => setTabletExpanded(true)}
        onMouseLeave={() => setTabletExpanded(false)}
      >
        {sidebarContent({ collapsed: !tabletExpanded })}
      </aside>

      {/* ==================== Desktop sidebar (> 1024) ==================== */}
      <aside className="hidden lg:flex h-screen w-60 flex-col bg-slate-900 shrink-0">
        {sidebarContent({})}
      </aside>
    </>
  );
}
