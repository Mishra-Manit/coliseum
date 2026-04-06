import type { ChartDataPoint } from "./types";

export type Interval = "1D" | "1W" | "1M";

export interface LWPoint {
  time: string;
  value: number;
}

export interface LWHistPoint {
  time: string;
  value: number;
  color: string;
}

const HIST_GREEN = "rgba(22, 163, 74, 0.65)";
const HIST_RED = "rgba(220, 38, 38, 0.65)";

function toDateKey(iso: string): string {
  return iso.slice(0, 10);
}

function isoWeekMonday(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + diff);
  return date.toISOString().split("T")[0];
}

function periodKey(dateStr: string, interval: Interval): string {
  if (interval === "1D") return dateStr;
  if (interval === "1W") return isoWeekMonday(dateStr);
  const [y, m] = dateStr.split("-");
  return `${y}-${m}-01`;
}

interface BucketAccumulator {
  date: string;
  firstNav: number;
  lastNav: number;
}

/**
 * Downsample a time-series of NAV snapshots into period buckets.
 * Each bucket keeps the last NAV value (for the area chart) and computes
 * the period PnL as (lastNav - firstNav) for the histogram.
 */
function bucketize(
  series: ChartDataPoint[],
  interval: Interval,
): { area: LWPoint[]; hist: LWHistPoint[] } {
  if (series.length === 0) return { area: [], hist: [] };

  const buckets = new Map<string, BucketAccumulator>();

  for (const point of series) {
    const dayStr = toDateKey(point.timestamp);
    const key = periodKey(dayStr, interval);
    const existing = buckets.get(key);
    if (!existing) {
      buckets.set(key, { date: key, firstNav: point.nav, lastNav: point.nav });
    } else {
      existing.lastNav = point.nav;
    }
  }

  const sorted = Array.from(buckets.values()).sort((a, b) =>
    a.date.localeCompare(b.date),
  );

  const area: LWPoint[] = sorted.map((b) => ({ time: b.date, value: b.lastNav }));
  const hist: LWHistPoint[] = sorted.map((b) => {
    const pnl = b.lastNav - b.firstNav;
    return {
      time: b.date,
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
  return bucketize(series, interval);
}
