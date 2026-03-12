import useSWR from "swr";
import { fetcher } from "@/lib/api";
import {
  mockPortfolioState,
  mockOpportunities,
  mockOpportunityDetails,
  mockDaemonStatus,
  mockLedgerEntries,
  mockChartData,
} from "@/lib/mock-data";
import type {
  PortfolioState,
  OpportunitySummary,
  OpportunityDetail,
  ColiseumConfig,
  DaemonStatus,
  LedgerEntry,
  ChartResponse,
} from "@/lib/types";

// Flag to use mock data (set to true when backend is unavailable)
const USE_MOCK_DATA = true;

// Mock-aware fetcher that falls back to mock data
function createMockFetcher<T>(mockData: T) {
  return async (url: string): Promise<T> => {
    if (USE_MOCK_DATA) {
      // Simulate network delay for realistic feel
      await new Promise((resolve) => setTimeout(resolve, 300));
      return mockData;
    }
    return fetcher<T>(url);
  };
}

export function useConfig() {
  // Mock config with realistic settings
  const mockConfig: ColiseumConfig = {
    trading: { paper_mode: true },
    risk: { max_position_size: 25, max_daily_loss: 50 },
    scout: { scan_interval_minutes: 15 },
    analyst: { max_research_time_seconds: 120 },
    guardian: { stop_loss_price: 0.15 },
    execution: { 
      order_check_interval_seconds: 30,
      max_order_age_minutes: 5,
      max_reprice_attempts: 3,
    },
    daemon: {
      heartbeat_interval_minutes: 5,
      guardian_interval_minutes: 2,
      max_consecutive_failures: 3,
    },
    telegram: {},
  };
  return useSWR<ColiseumConfig>(
    "/api/config",
    createMockFetcher(mockConfig),
    { refreshInterval: 30000 }
  );
}

export function usePortfolioState() {
  return useSWR<PortfolioState>(
    "/api/state",
    createMockFetcher(mockPortfolioState),
    { refreshInterval: 15000 }
  );
}

export function useOpportunities() {
  return useSWR<OpportunitySummary[]>(
    "/api/opportunities",
    createMockFetcher(mockOpportunities),
    { refreshInterval: 30000 }
  );
}

export function useOpportunityDetail(id: string | null) {
  const mockFetcher = async (url: string): Promise<OpportunityDetail> => {
    if (USE_MOCK_DATA) {
      await new Promise((resolve) => setTimeout(resolve, 200));
      const detail = mockOpportunityDetails[id!];
      if (detail) return detail;
      // For opportunities without detailed mock data, generate a basic one
      const summary = mockOpportunities.find((o) => o.id === id);
      if (summary) {
        return {
          summary,
          markdown_body: `# ${summary.title}\n\n**Event**: ${summary.event_title}\n\n## Research Summary\n\nDetailed analysis pending. Market currently trading at ${Math.round(summary.yes_price * 100)}c YES / ${Math.round(summary.no_price * 100)}c NO.\n\n### Status: ${summary.status.toUpperCase()}\n\n${summary.action ? `**Recommendation**: ${summary.action}` : "No action recommended at this time."}`,
          raw_frontmatter: {},
        };
      }
      throw new Error("Opportunity not found");
    }
    return fetcher<OpportunityDetail>(url);
  };

  return useSWR<OpportunityDetail>(
    id ? `/api/opportunities/${id}` : null,
    mockFetcher,
    { refreshInterval: 30000 }
  );
}

export function usePipelineStatus() {
  return useSWR<{ running: boolean }>(
    "/api/pipeline/status",
    createMockFetcher({ running: false }),
    { refreshInterval: 3000 }
  );
}

export function useDaemonStatus() {
  return useSWR<DaemonStatus>(
    "/api/daemon/status",
    createMockFetcher(mockDaemonStatus),
    { refreshInterval: 10000 }
  );
}

export function useLedger(limit = 100) {
  const limitedEntries = mockLedgerEntries.slice(0, limit);
  return useSWR<LedgerEntry[]>(
    `/api/ledger?limit=${limit}`,
    createMockFetcher(limitedEntries),
    { refreshInterval: 15000 }
  );
}

export function useChartData() {
  return useSWR<ChartResponse>(
    "/api/chart",
    createMockFetcher(mockChartData),
    { refreshInterval: 30000 }
  );
}
