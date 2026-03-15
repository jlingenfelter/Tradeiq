"use client";

import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useSubscription, useCreateCheckout } from "@/hooks/use-subscription";
import { Check, Sparkles, Crown, Users } from "lucide-react";

const PLANS = [
  {
    id: "free" as const,
    name: "Free",
    price: "$0",
    period: "forever",
    icon: Sparkles,
    description: "Get started tracking your wealth",
    features: [
      "Manual asset & liability entry",
      "1 portfolio",
      "3 connected accounts",
      "90-day net worth history",
      "Basic goal tracking",
      "AI insights (limited)",
      "Smart alerts (in-app)",
    ],
    cta: "Current Plan",
    highlight: false,
  },
  {
    id: "pro" as const,
    name: "Pro",
    price: "$10",
    period: "/month",
    icon: Crown,
    description: "For serious wealth builders",
    features: [
      "Everything in Free, plus:",
      "Unlimited portfolios",
      "Unlimited connected accounts",
      "Plaid & Open Banking sync",
      "Full net worth history",
      "CSV & PDF exports",
      "Scenario modeling",
      "Email notifications",
      "Full goal projections",
      "Custom reports",
      "API access (1,000 req/day)",
    ],
    cta: "Upgrade to Pro",
    highlight: true,
  },
  {
    id: "family" as const,
    name: "Family",
    price: "$18",
    period: "/month",
    icon: Users,
    description: "Track wealth together",
    features: [
      "Everything in Pro, plus:",
      "Up to 3 household members",
      "Combined net worth view",
      "Shared goals",
      "Document vault",
      "Priority support",
    ],
    cta: "Upgrade to Family",
    highlight: false,
  },
];

export default function PricingPage() {
  const { data: subscription } = useSubscription();
  const checkout = useCreateCheckout();
  const currentTier = subscription?.tier || "free";

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold">Choose Your Plan</h2>
          <p className="text-neutral-500 mt-2">
            Unlock powerful wealth tracking features. Cancel anytime.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => {
            const isCurrent = currentTier === plan.id;
            const isDowngrade =
              plan.id === "free" && currentTier !== "free";

            return (
              <Card
                key={plan.id}
                className={`relative ${
                  plan.highlight
                    ? "border-2 border-indigo-500 shadow-lg shadow-indigo-100"
                    : "border"
                }`}
              >
                {plan.highlight && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-indigo-600 text-white hover:bg-indigo-600">
                      Most Popular
                    </Badge>
                  </div>
                )}
                <CardContent className="p-6 pt-8 space-y-6">
                  <div>
                    <div className="flex items-center gap-2">
                      <plan.icon className={`h-5 w-5 ${plan.highlight ? "text-indigo-600" : "text-neutral-600"}`} />
                      <h3 className="text-lg font-semibold">{plan.name}</h3>
                    </div>
                    <p className="text-sm text-neutral-500 mt-1">{plan.description}</p>
                  </div>

                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold">{plan.price}</span>
                    <span className="text-neutral-500 text-sm">{plan.period}</span>
                  </div>

                  <Button
                    className={`w-full ${
                      plan.highlight
                        ? "bg-indigo-600 hover:bg-indigo-700 text-white"
                        : ""
                    }`}
                    variant={plan.highlight ? "default" : "outline"}
                    disabled={isCurrent || isDowngrade || checkout.isPending}
                    onClick={() => {
                      if (plan.id !== "free") {
                        checkout.mutate(plan.id);
                      }
                    }}
                  >
                    {isCurrent ? "Current Plan" : isDowngrade ? "—" : plan.cta}
                  </Button>

                  <ul className="space-y-2.5">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <Check className={`h-4 w-4 mt-0.5 shrink-0 ${plan.highlight ? "text-indigo-600" : "text-green-600"}`} />
                        <span className={i === 0 && plan.id !== "free" ? "font-medium" : "text-neutral-600"}>
                          {feature}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="text-center text-sm text-neutral-400">
          All plans include end-to-end encryption. No trading, no financial advice.
          <br />
          Questions? Contact support@tradeiq.app
        </div>
      </div>
    </AppShell>
  );
}
