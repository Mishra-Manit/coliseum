import useSWR from "swr";
import { fetcher } from "@/lib/api";
import type {
  PortfolioState,
  OpportunitySummary,
  OpportunityDetail,
  ColiseumConfig,
  DaemonStatus,
  LedgerEntry,
  ChartResponse,
} from "@/lib/types";

export function useConfig() {
  return useSWR<ColiseumConfig>("/api/config", fetcher, {
    refreshInterval: 300_000,
  });
}

export function usePortfolioState() {
  return useSWR<PortfolioState>("/api/state", fetcher, {
    refreshInterval: 120_000,
  });
}

export function useOpportunities() {
  return useSWR<OpportunitySummary[]>("/api/opportunities", fetcher, {
    refreshInterval: 120_000,
  });
}

export function useOpportunityDetail(id: string | null) {
  return useSWR<OpportunityDetail>(
    id ? `/api/opportunities/${id}` : null,
    fetcher,
    { refreshInterval: 120_000 }
  );
}

export function usePipelineStatus() {
  return useSWR<{ running: boolean }>("/api/pipeline/status", fetcher, {
    refreshInterval: 5_000,
  });
}

export function useDaemonStatus() {
  return useSWR<DaemonStatus>("/api/daemon/status", fetcher, {
    refreshInterval: 30_000,
  });
}

export function useLedger(limit = 100) {
  return useSWR<LedgerEntry[]>(`/api/ledger?limit=${limit}`, fetcher, {
    refreshInterval: 60_000,
  });
}

export function useChartData() {
  return useSWR<ChartResponse>("/api/chart", fetcher, {
    refreshInterval: 120_000,
  });
}
