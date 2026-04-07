import type { ChartDataPoint } from "./types";

export type Interval = "1D" | "1W" | "1M";

export interface LWPoint {
  time: number;
  value: number;
}

export interface LWHistPoint {
  time: number;
  value: number;
  color: string;
}

const HIST_GREEN = "rgba(22, 163, 74, 0.65)";
const HIST_RED = "rgba(220, 38, 38, 0.65)";

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

interface BucketAccumulator {
  time: number;
  firstNav: number;
  lastNav: number;
}

function toUnixSeconds(ms: number): number {
  return Math.floor(ms / 1000);
}

function parseTimestamp(iso: string): number {
  return new Date(iso).getTime();
}

function getCutoffMs(latestMs: number, interval: Interval): number {
  if (interval === "1D") return latestMs - DAY_MS;
  if (interval === "1W") return latestMs - 7 * DAY_MS;
  return latestMs - 30 * DAY_MS;
}

function getBucketMs(timestampMs: number, interval: Interval): number {
  if (interval === "1D") {
    return Math.floor(timestampMs / HOUR_MS) * HOUR_MS;
  }
  return Math.floor(timestampMs / DAY_MS) * DAY_MS;
}

function getFilteredSeries(
  series: ChartDataPoint[],
  interval: Interval,
): ChartDataPoint[] {
  if (series.length === 0) return [];

  const sorted = [...series].sort(
    (a, b) => parseTimestamp(a.timestamp) - parseTimestamp(b.timestamp),
  );

  const latestMs = parseTimestamp(sorted[sorted.length - 1].timestamp);
  const cutoffMs = getCutoffMs(latestMs, interval);

  return sorted.filter((point) => parseTimestamp(point.timestamp) >= cutoffMs);
}

function bucketize(
  series: ChartDataPoint[],
  interval: Interval,
): { area: LWPoint[]; hist: LWHistPoint[] } {
  if (series.length === 0) return { area: [], hist: [] };

  const buckets = new Map<number, BucketAccumulator>();

  for (const point of series) {
    const timestampMs = parseTimestamp(point.timestamp);
    const bucketMs = getBucketMs(timestampMs, interval);
    const existing = buckets.get(bucketMs);

    if (!existing) {
      buckets.set(bucketMs, {
        time: toUnixSeconds(bucketMs),
        firstNav: point.nav,
        lastNav: point.nav,
      });
      continue;
    }

    existing.lastNav = point.nav;
  }

  const sorted = Array.from(buckets.values()).sort((a, b) => a.time - b.time);

  const area: LWPoint[] = sorted.map((bucket) => ({
    time: bucket.time,
    value: bucket.lastNav,
  }));

  const hist: LWHistPoint[] = sorted.map((bucket) => {
    const pnl = bucket.lastNav - bucket.firstNav;
    return {
      time: bucket.time,
      value: Math.round(pnl * 100) / 100,
      color: pnl >= 0 ? HIST_GREEN : HIST_RED,
    };
  });

  return { area, hist };
}

export function getChartSeries(
  series: ChartDataPoint[],
  interval: Interval,
): { area: LWPoint[]; hist: LWHistPoint[] } {
  const filtered = getFilteredSeries(series, interval);
  return bucketize(filtered, interval);
}
