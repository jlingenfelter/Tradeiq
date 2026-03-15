// Auth
export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Portfolio
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

// Analytics
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
  id: string;
  warning_type: string;
  severity: WarningSeverity;
  title: string;
  description: string;
  evidence_json: Record<string, unknown>;
  triggered_at: string;
}

// Dashboard
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

// Chat
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  portfolio_id: string;
  created_at: string;
  updated_at: string;
}

// Alerts
export interface AlertSubscription {
  id: string;
  portfolio_id: string;
  alert_type: string;
  threshold_json: Record<string, unknown>;
  channel: string;
  enabled: boolean;
}
