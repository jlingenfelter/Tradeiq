"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import type { TokenResponse } from "@/types";
import {
  Check,
  Mail,
  Lock,
  TrendingUp,
  Shield,
  Brain,
  PieChart,
} from "lucide-react";

const FEATURES = [
  { icon: PieChart, text: "Track all your investments in one place" },
  { icon: Brain, text: "AI-powered insights and forecasting" },
  { icon: Shield, text: "Bank-grade encryption and security" },
  { icon: TrendingUp, text: "Real-time portfolio analytics" },
];

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.post<TokenResponse>("/auth/login", { email, password });
      login(res.access_token, res.user);
      router.push("/overview");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900">
        {/* Gradient mesh / orbs */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-24 -left-24 w-96 h-96 rounded-full bg-indigo-500/20 blur-3xl animate-pulse" />
          <div className="absolute top-1/2 -right-24 w-80 h-80 rounded-full bg-purple-500/15 blur-3xl animate-pulse [animation-delay:2s]" />
          <div className="absolute bottom-0 left-1/3 w-72 h-72 rounded-full bg-blue-500/10 blur-3xl animate-pulse [animation-delay:4s]" />
        </div>
        {/* Grid pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />

        <div className="relative z-10 flex flex-col justify-center px-12 xl:px-20 w-full">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <span className="text-white text-lg font-bold">T</span>
            </div>
            <span className="text-2xl font-bold text-white tracking-tight">
              TradeIQ
            </span>
          </div>

          {/* Tagline */}
          <h1 className="text-4xl xl:text-5xl font-bold text-white leading-tight mb-4">
            Your complete
            <br />
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              wealth command center
            </span>
          </h1>
          <p className="text-slate-400 text-lg mb-10 max-w-md">
            Monitor, analyze, and grow your portfolio with intelligent tools
            built for modern investors.
          </p>

          {/* Feature bullets */}
          <ul className="space-y-4 mb-14">
            {FEATURES.map((f, i) => (
              <li key={i} className="flex items-center gap-3">
                <div className="flex items-center justify-center h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                  <f.icon className="h-4 w-4 text-indigo-400" />
                </div>
                <span className="text-slate-300 text-sm">{f.text}</span>
              </li>
            ))}
          </ul>

          {/* Social proof */}
          <div className="flex items-center gap-3">
            <div className="flex -space-x-2">
              {[
                "bg-indigo-500",
                "bg-purple-500",
                "bg-blue-500",
                "bg-emerald-500",
              ].map((bg, i) => (
                <div
                  key={i}
                  className={`h-8 w-8 rounded-full ${bg} border-2 border-slate-900 flex items-center justify-center`}
                >
                  <span className="text-white text-xs font-medium">
                    {["J", "S", "M", "A"][i]}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-slate-400 text-sm">
              Trusted by{" "}
              <span className="text-white font-semibold">2,400+</span>{" "}
              investors
            </p>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex flex-col">
        {/* Mobile branding strip */}
        <div className="lg:hidden bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 px-6 py-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center">
              <span className="text-white text-sm font-bold">T</span>
            </div>
            <span className="text-xl font-bold text-white">TradeIQ</span>
          </div>
          <p className="text-slate-400 text-sm">
            Your complete wealth command center
          </p>
        </div>

        <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
          <div className="w-full max-w-sm">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-slate-900">
                Welcome back
              </h2>
              <p className="text-slate-500 mt-1">
                Sign in to your TradeIQ account
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="rounded-lg bg-red-50 border border-red-100 p-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-slate-700 text-sm font-medium">
                  Email address
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com"
                    className="pl-10 h-11 border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-slate-700 text-sm font-medium">
                    Password
                  </Label>
                  <Link
                    href="/forgot-password"
                    className="text-xs text-indigo-600 hover:text-indigo-500 font-medium"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 h-11 border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-11 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-700 hover:to-indigo-600 text-white font-medium shadow-md shadow-indigo-500/25 cursor-pointer"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign in"}
              </Button>

              <p className="text-center text-sm text-slate-500">
                Don&apos;t have an account?{" "}
                <Link
                  href="/signup"
                  className="text-indigo-600 font-semibold hover:text-indigo-500"
                >
                  Sign up
                </Link>
              </p>
            </form>

            {/* Trust indicators */}
            <div className="mt-10 pt-6 border-t border-slate-100">
              <div className="flex items-center justify-center gap-6 text-xs text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5" />
                  <span>256-bit encryption</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5" />
                  <span>SOC 2 compliant</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
