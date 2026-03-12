"use client";

import { useState, useEffect, useRef } from "react";
import type { PortfolioStreamPayload, EnrichedPosition } from "@/lib/types";
import { mockPortfolioState } from "@/lib/mock-data";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const SSE_URL = `${API_BASE}/api/stream/portfolio`;
const RECONNECT_DELAY_MS = 3000;

// Flag to use mock data (matches use-api.ts)
const USE_MOCK_DATA = true;

// Create enriched positions from mock data for the stream
function createMockStreamData(): PortfolioStreamPayload {
  const enrichedPositions: EnrichedPosition[] = mockPortfolioState.open_positions.map((pos) => {
    const unrealizedPnl = (pos.current_price - pos.average_entry) * pos.contracts;
    const pctChange = ((pos.current_price - pos.average_entry) / pos.average_entry) * 100;
    return {
      ...pos,
      unrealized_pnl: unrealizedPnl,
      pct_change: pctChange,
    };
  });

  return {
    open_positions: enrichedPositions,
    portfolio: mockPortfolioState.portfolio,
    timestamp: Date.now(),
  };
}

export function usePortfolioStream(): {
  data: PortfolioStreamPayload | null;
  connected: boolean;
  error: string | null;
} {
  const [data, setData] = useState<PortfolioStreamPayload | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Use mock data if enabled
    if (USE_MOCK_DATA) {
      setData(createMockStreamData());
      setConnected(true);
      setError(null);
      
      // Simulate periodic updates with slight price variations
      const interval = setInterval(() => {
        const mockData = createMockStreamData();
        // Add small random variations to simulate live data
        mockData.open_positions = mockData.open_positions.map((pos) => {
          const variation = (Math.random() - 0.5) * 0.02; // +/- 1%
          const newPrice = Math.max(0.01, Math.min(0.99, pos.current_price + variation));
          const unrealizedPnl = (newPrice - pos.average_entry) * pos.contracts;
          const pctChange = ((newPrice - pos.average_entry) / pos.average_entry) * 100;
          return {
            ...pos,
            current_price: newPrice,
            unrealized_pnl: unrealizedPnl,
            pct_change: pctChange,
          };
        });
        mockData.timestamp = Date.now();
        setData(mockData);
      }, 5000);

      return () => clearInterval(interval);
    }

    function connect() {
      const es = new EventSource(SSE_URL);
      esRef.current = es;

      es.onopen = () => {
        setConnected(true);
        setError(null);
      };

      es.onmessage = (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data as string) as PortfolioStreamPayload;
          if (parsed.error) {
            setError(parsed.error);
          } else {
            setData(parsed);
            setError(null);
          }
        } catch {
          // malformed frame — ignore
        }
      };

      es.onerror = () => {
        setConnected(false);
        es.close();
        if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
      };
    }

    connect();

    return () => {
      esRef.current?.close();
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    };
  }, []);

  return { data, connected, error };
}
