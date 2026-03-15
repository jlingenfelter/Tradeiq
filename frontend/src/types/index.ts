// Auth
export interface User {
  id: string;
  email: string;
  base_currency: string;
  timezone: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Portfolio (investment submodule)
export interface Portfolio {
  id: string;
  name: string;
  base_currency: string;
  created_at: string;
  updated_at: string;
}

export interface Account {
  id: string;
  portfolio_id: string;
  name: string;
  source_type: "manual" | "csv" | "broker";
  created_at: string;
}

export interface Position {
  id: string;
  account_id: string;
  symbol: string;
  asset_name: string;
  asset_type: string;
  quantity: number;
  cost_basis_total: number | null;
  cost_basis_per_share: number | null;
  currency: string;
  current_price?: number;
  market_value?: number;
  weight?: number;
  unrealized_pnl?: number;
  sector?: string;
  country?: string;
}

// Analytics (portfolio-level)
export interface AnalyticsSnapshot {
  id: string;
  portfolio_id: string;
  health_score: number;
  top_holding_weight: number;
  top_3_weight: number;
  top_5_weight: number;
  sector_concentration_score: number;
  country_concentration_score: number;
  diversification_score: number;
  created_at: string;
}

export interface StressTestResult {
  scenario: string;
  portfolio_impact_pct: number;
  portfolio_impact_value: number;
  top_contributors: { symbol: string; impact: number }[];
}

export interface HealthScoreBreakdown {
  overall: number;
  diversification: number;
  single_stock_concentration: number;
  sector_concentration: number;
  event_risk: number;
  benchmark_balance: number;
  resilience: number;
}

// Warnings
export type WarningSeverity = "info" | "medium" | "high" | "critical";

export interface Warning {
  id?: string;
  warning_type: string;
  severity: WarningSeverity;
  title: string;
  description: string;
  evidence_json?: Record<string, unknown>;
  evidence?: Record<string, unknown>;
  triggered_at?: string;
}

// Portfolio Dashboard
export interface DashboardResponse {
  portfolio_id: string;
  portfolio_name: string;
  base_currency: string;
  total_value: number;
  daily_change: number;
  daily_change_pct: number;
  health_score: number;
  health_score_breakdown: HealthScoreBreakdown;
  top_risks: Warning[];
  top_holdings: {
    symbol: string;
    name: string;
    weight: number;
    market_value: number;
  }[];
  sector_exposure: { sector: string; weight: number }[];
  country_exposure: { country: string; weight: number }[];
  stress_tests: StressTestResult[];
  ai_summary: string | null;
}

// ── Wealth Tracking ──

export interface WealthContainer {
  id: string;
  name: string;
  container_type: string;
  institution_name: string | null;
  currency: string;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  container_id: string | null;
  asset_class: string;
  asset_subclass: string | null;
  name: string;
  symbol: string | null;
  quantity: number | null;
  unit_value: number | null;
  current_value: number;
  cost_basis: number | null;
  currency: string;
  ownership_pct: number | null;
  liquidity_category: string;
  valuation_source: string;
  valuation_date: string;
  country: string | null;
  sector: string | null;
  notes: string | null;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface Liability {
  id: string;
  container_id: string | null;
  liability_type: string;
  name: string;
  current_balance: number;
  currency: string;
  interest_rate: number | null;
  monthly_payment: number | null;
  due_date: string | null;
  linked_asset_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AllocationItem {
  category: string;
  value: number;
  weight: number;
}

export interface ConcentrationItem {
  label: string;
  value: number;
  weight_of_assets: number;
}

export interface WealthHealthBreakdown {
  overall: number;
  liquidity: number;
  concentration: number;
  leverage: number;
  diversification: number;
  data_freshness: number;
  public_market_risk: number;
}

export interface WealthHolding {
  name: string;
  symbol: string | null;
  category: string;
  asset_class: string;
  value: number;
  weight: number;
  currency: string;
  country: string | null;
  sector: string | null;
  source: string;
}

export interface WealthDashboardResponse {
  base_currency: string;
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  net_worth_change_30d: number | null;
  liquid_assets: number;
  illiquid_assets: number;
  liquid_net_worth: number;
  cash_value: number;
  investment_value: number;
  property_value: number;
  crypto_value: number;
  business_value: number;
  pension_value: number;
  other_asset_value: number;
  debt_value: number;
  allocation: AllocationItem[];
  top_concentrations: ConcentrationItem[];
  top_warnings: Warning[];
  health_score: number;
  health_score_breakdown: WealthHealthBreakdown;
  ai_summary: string | null;
  holdings: WealthHolding[];
}

export interface NetWorthHistoryItem {
  date: string;
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  liquid_assets: number;
}

// Chat
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  portfolio_id: string | null;
  created_at: string;
  updated_at: string;
}

// Alerts
export interface AlertSubscription {
  id: string;
  alert_type: string;
  threshold_json: Record<string, unknown>;
  channel: string;
  enabled: boolean;
}

// Asset class constants
export const ASSET_CLASSES = [
  "cash",
  "stock",
  "etf",
  "mutual_fund",
  "bond",
  "pension",
  "crypto",
  "property",
  "business_equity",
  "gold",
  "watch",
  "collectible",
  "private_loan_receivable",
  "other",
] as const;

export const LIABILITY_TYPES = [
  "mortgage",
  "loan",
  "credit_card",
  "tax",
  "margin",
  "business_debt",
  "other",
] as const;

export const LIQUIDITY_CATEGORIES = [
  "highly_liquid",
  "liquid",
  "semi_liquid",
  "illiquid",
] as const;

export const CONTAINER_TYPES = [
  "brokerage",
  "pension",
  "bank",
  "crypto_wallet",
  "property",
  "business",
  "liability_account",
  "collectibles",
  "manual",
] as const;
