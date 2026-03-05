import useSWR from "swr";
import { fetcher } from "@/lib/api";
import type {
  PortfolioState,
  OpportunitySummary,
  OpportunityDetail,
  ColiseumConfig,
  DaemonStatus,
} from "@/lib/types";

export function useConfig() {
  return useSWR<ColiseumConfig>("/api/config", fetcher, {
    refreshInterval: 30000,
  });
}

export function usePortfolioState() {
  return useSWR<PortfolioState>("/api/state", fetcher, {
    refreshInterval: 15000,
  });
}

export function useOpportunities() {
  return useSWR<OpportunitySummary[]>("/api/opportunities", fetcher, {
    refreshInterval: 30000,
  });
}

export function useOpportunityDetail(id: string | null) {
  return useSWR<OpportunityDetail>(
    id ? `/api/opportunities/${id}` : null,
    fetcher,
    { refreshInterval: 30000 }
  );
}

export function usePipelineStatus() {
  return useSWR<{ running: boolean }>("/api/pipeline/status", fetcher, {
    refreshInterval: 3000,
  });
}

export function useDaemonStatus() {
  return useSWR<DaemonStatus>("/api/daemon/status", fetcher, {
    refreshInterval: 10000,
  });
}
