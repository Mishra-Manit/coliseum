import type { ChartDataPoint } from "./types";

export type Interval = "1D" | "1W" | "1M" | "ALL";

export interface LWPoint {
  time: number;
  value: number;
}

export interface LWHistPoint extends LWPoint {
  color: string;
}

const HIST_GREEN = "rgba(22, 163, 74, 0.65)";
const HIST_RED = "rgba(220, 38, 38, 0.65)";

const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * HOUR_MS;

function getCutoffMs(latestMs: number, interval: Interval): number | null {
  if (interval === "1D") return latestMs - DAY_MS;
  if (interval === "1W") return latestMs - 7 * DAY_MS;
  if (interval === "1M") return latestMs - 30 * DAY_MS;
  return null;
}

function getBucketMs(timestampMs: number, interval: Interval): number {
  if (interval === "1D") return Math.floor(timestampMs / HOUR_MS) * HOUR_MS;
  return Math.floor(timestampMs / DAY_MS) * DAY_MS;
}

function getFilteredSeries(
  series: ChartDataPoint[],
  interval: Interval,
): ChartDataPoint[] {
  if (series.length === 0) return [];

  const sorted = [...series].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
  const cutoffMs = getCutoffMs(
    new Date(sorted[sorted.length - 1].timestamp).getTime(),
    interval,
  );

  if (cutoffMs === null) return sorted;
  return sorted.filter((point) => new Date(point.timestamp).getTime() >= cutoffMs);
}

function bucketize(
  series: ChartDataPoint[],
  interval: Interval,
): { area: LWPoint[]; hist: LWHistPoint[] } {
  if (series.length === 0) return { area: [], hist: [] };

  const buckets = new Map<
    number,
    { time: number; firstNav: number; lastNav: number }
  >();

  for (const point of series) {
    const timestampMs = new Date(point.timestamp).getTime();
    const bucketMs = getBucketMs(timestampMs, interval);
    const existing = buckets.get(bucketMs);

    buckets.set(bucketMs, {
      time: Math.floor(bucketMs / 1000),
      firstNav: existing?.firstNav ?? point.nav,
      lastNav: point.nav,
    });
  }

  const bucketValues = Array.from(buckets.values()).sort((a, b) => a.time - b.time);
  return {
    area: bucketValues.map((bucket) => ({
      time: bucket.time,
      value: bucket.lastNav,
    })),
    hist: bucketValues.map((bucket) => {
      const pnl = bucket.lastNav - bucket.firstNav;
      return {
        time: bucket.time,
        value: Math.round(pnl * 100) / 100,
        color: pnl >= 0 ? HIST_GREEN : HIST_RED,
      };
    }),
  };
}

export function getChartSeries(
  series: ChartDataPoint[],
  interval: Interval,
): { area: LWPoint[]; hist: LWHistPoint[] } {
  return bucketize(getFilteredSeries(series, interval), interval);
}
