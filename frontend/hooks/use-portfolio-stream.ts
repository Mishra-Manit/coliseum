"use client";

import { useState, useEffect, useRef } from "react";
import type { PortfolioStreamPayload } from "@/lib/types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "https://coliseumapi.manitmishra.com";
const SSE_URL = `${API_BASE}/api/stream/portfolio`;
const RECONNECT_DELAY_MS = 3000;

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
