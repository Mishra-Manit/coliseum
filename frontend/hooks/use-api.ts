import useSWR from "swr";
import { fetcher } from "@/lib/api";
import type {
  PortfolioState,
  OpportunitySummary,
  OpportunityDetail,
  AgentStatusResponse,
  AgentActivity,
  KalshiBalance,
  KalshiPosition,
  KalshiOrder,
} from "@/lib/types";

export function usePortfolioState() {
  return useSWR<PortfolioState>("/api/status", fetcher, {
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

export function useAgentStatus() {
  return useSWR<AgentStatusResponse>("/api/agents", fetcher, {
    refreshInterval: 10000,
  });
}

export function useAgentActivity() {
  return useSWR<AgentActivity[]>("/api/agents/activity", fetcher, {
    refreshInterval: 15000,
  });
}

export function useKalshiBalance() {
  return useSWR<KalshiBalance>("/api/kalshi/balance", fetcher, {
    refreshInterval: 30000,
  });
}

export function useKalshiPositions() {
  return useSWR<KalshiPosition[]>("/api/kalshi/positions", fetcher, {
    refreshInterval: 15000,
  });
}

export function useKalshiOrders() {
  return useSWR<KalshiOrder[]>("/api/kalshi/orders", fetcher, {
    refreshInterval: 15000,
  });
}
