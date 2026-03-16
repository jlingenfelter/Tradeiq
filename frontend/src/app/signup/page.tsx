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
  ChevronDown,
  User,
} from "lucide-react";

const CURRENCIES = ["USD", "GBP", "EUR", "CHF", "CAD", "AUD", "JPY", "SGD", "HKD"];

const FEATURES = [
  { icon: PieChart, text: "Track all your investments in one place" },
  { icon: Brain, text: "AI-powered insights and forecasting" },
  { icon: Shield, text: "Bank-grade encryption and security" },
  { icon: TrendingUp, text: "Real-time portfolio analytics" },
];

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [baseCurrency, setBaseCurrency] = useState("USD");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      const res = await api.post<TokenResponse>("/auth/signup", {
        email,
        password,
        name,
        base_currency: baseCurrency,
      });
      login(res.access_token, res.user);
      router.push("/overview");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Signup failed");
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
            Start building
            <br />
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              your wealth today
            </span>
          </h1>
          <p className="text-slate-400 text-lg mb-10 max-w-md">
            Join thousands of investors using TradeIQ to monitor, analyze, and
            grow their portfolios.
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
            Start building your wealth today
          </p>
        </div>

        <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
          <div className="w-full max-w-sm">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-slate-900">
                Create your account
              </h2>
              <p className="text-slate-500 mt-1">
                Get started free — no credit card required
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="rounded-lg bg-red-50 border border-red-100 p-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="name" className="text-slate-700 text-sm font-medium">
                  Full name
                </Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="name"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="John Doe"
                    className="pl-10 h-11 border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
                  />
                </div>
              </div>

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
                <Label htmlFor="password" className="text-slate-700 text-sm font-medium">
                  Password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 8 characters"
                    className="pl-10 h-11 border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="confirm" className="text-slate-700 text-sm font-medium">
                  Confirm password
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    id="confirm"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="pl-10 h-11 border-slate-200 focus:border-indigo-500 focus:ring-indigo-500"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="currency" className="text-slate-700 text-sm font-medium">
                  Base currency
                </Label>
                <div className="relative">
                  <select
                    id="currency"
                    className="w-full h-11 rounded-md border border-slate-200 bg-white px-3 pr-10 text-sm text-slate-900 appearance-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none"
                    value={baseCurrency}
                    onChange={(e) => setBaseCurrency(e.target.value)}
                  >
                    {CURRENCIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-11 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-700 hover:to-indigo-600 text-white font-medium shadow-md shadow-indigo-500/25 cursor-pointer"
                disabled={loading}
              >
                {loading ? "Creating account..." : "Get started free"}
              </Button>

              <p className="text-center text-sm text-slate-500">
                Already have an account?{" "}
                <Link
                  href="/login"
                  className="text-indigo-600 font-semibold hover:text-indigo-500"
                >
                  Sign in
                </Link>
              </p>
            </form>

            {/* Trust indicators */}
            <div className="mt-8 pt-6 border-t border-slate-100">
              <div className="flex items-center justify-center gap-6 text-xs text-slate-400">
                <div className="flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5" />
                  <span>256-bit encryption</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Check className="h-3.5 w-3.5" />
                  <span>No credit card required</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
