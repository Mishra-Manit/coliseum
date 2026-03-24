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

function isoWeekMonday(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + diff);
  return date.toISOString().split("T")[0];
}

function aggregateByPeriod(
  daily: ChartDataPoint[],
  interval: Exclude<Interval, "1D">
): ChartDataPoint[] {
  const periodKey = (date: string): string => {
    const [y, m] = date.split("-");
    if (interval === "1W") return isoWeekMonday(date);
    return `${y}-${m}-01`;
  };

  const groups = new Map<string, ChartDataPoint>();
  for (const point of daily) {
    const key = periodKey(point.date);
    const existing = groups.get(key);
    if (!existing) {
      groups.set(key, { ...point, date: key });
    } else {
      groups.set(key, {
        ...existing,
        cumulative_pnl: point.cumulative_pnl,
        pnl: existing.pnl + point.pnl,
        trades: existing.trades + point.trades,
        wins: existing.wins + point.wins,
        losses: existing.losses + point.losses,
        nav: point.nav,
      });
    }
  }

  return Array.from(groups.values()).sort((a, b) =>
    a.date.localeCompare(b.date)
  );
}

export function getChartSeries(
  daily: ChartDataPoint[],
  interval: Interval
): { area: LWPoint[]; hist: LWHistPoint[] } {
  const points =
    interval === "1D" ? daily : aggregateByPeriod(daily, interval);
  return {
    area: points.map((p) => ({ time: p.date, value: p.nav })),
    hist: points.map((p) => ({
      time: p.date,
      value: p.pnl,
      color: p.pnl >= 0 ? HIST_GREEN : HIST_RED,
    })),
  };
}
