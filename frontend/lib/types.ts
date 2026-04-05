export interface PortfolioStats {
  total_value: number;
  cash_balance: number;
  positions_value: number;
}

export interface Position {
  id: string;
  market_ticker: string;
  side: string;
  contracts: number;
  average_entry: number;
  current_price: number;
  opportunity_id: string | null;
}

export interface EnrichedPosition extends Position {
  unrealized_pnl: number;
  pct_change: number;
}

export interface PortfolioState {
  portfolio: PortfolioStats;
  open_positions: EnrichedPosition[];
}

export interface ClosedPosition {
  market_ticker: string;
  side: string;
  contracts: number;
  entry_price: number;
  exit_price: number;
  pnl: number;
  opportunity_id: string | null;
  closed_at: string | null;
}

export interface OpportunitySummary {
  id: string;
  event_ticker: string;
  event_title: string;
  market_ticker: string;
  title: string;
  subtitle: string;
  yes_price: number;
  no_price: number;
  close_time: string;
  discovered_at: string;
  status: string;
  action: string | null;
  date_folder: string;
}

export interface ScoutSection {
  outcome_status: string;
  risk_level: string;
  summary: string;
  evidence: string[];
  resolution_source: string;
  remaining_risks: string[];
  sources: string[];
  is_structured: boolean;
}

export interface ResearchSection {
  flip_risk: "YES" | "NO" | "UNCERTAIN";
  confidence: "HIGH" | "MEDIUM" | "LOW" | null;
  event_status: string;
  evidence_for: string[];
  evidence_against: string[];
  resolution_mechanics: string;
  conclusion: string;
  unconfirmed: string[];
  sources: string[];
}

export interface TraderSection {
  decision: "EXECUTE_BUY_YES" | "EXECUTE_BUY_NO" | "REJECT";
  tldr: string;
}

export interface ParsedSections {
  scout: ScoutSection;
  research: ResearchSection | null;
  trader: TraderSection | null;
}

export interface OpportunityDetail {
  summary: OpportunitySummary;
  markdown_body: string;
  raw_frontmatter: Record<string, unknown>;
  parsed_sections: ParsedSections | null;
}

export interface ColiseumConfig {
  trading: Record<string, unknown>;
  risk: Record<string, unknown>;
  scout: Record<string, unknown>;
  guardian: Record<string, unknown>;
  execution: Record<string, unknown>;
  daemon: Record<string, unknown>;
  telegram: Record<string, unknown>;
}

export interface DaemonStatus {
  available: boolean;
  running: boolean;
  paused: boolean;
  uptime_seconds: number;
  cycles_completed: number;
  consecutive_failures: number;
  last_cycle: string | null;
}

export interface LedgerEntry {
  type: "buy" | "close";
  id: string;
  market_ticker: string;
  side: "YES" | "NO";
  contracts: number;
  price: number;
  pnl: number | null;
  opportunity_id: string | null;
  paper: boolean;
  timestamp: string;
}

export interface ChartDataPoint {
  date: string;
  pnl: number;
  cumulative_pnl: number;
  nav: number;
  trades: number;
  wins: number;
  losses: number;
}

export interface ChartStats {
  total_pnl: number;
  win_rate: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  best_day: number;
  worst_day: number;
  current_nav: number;
  initial_nav: number;
}

export interface ChartResponse {
  daily: ChartDataPoint[];
  stats: ChartStats;
}
