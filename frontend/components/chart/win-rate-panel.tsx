"use client";

import type { ChartStats } from "@/lib/types";
import { RadialGauge } from "./radial-gauge";
import { StatCard } from "./stat-card";

interface WinRatePanelProps {
  stats: ChartStats;
}

function formatDayAmount(value: number): string {
  if (value >= 0) return `+$${value.toFixed(2)}`;
  return `-$${Math.abs(value).toFixed(2)}`;
}

function formatBestDay(value: number): string {
  if (value <= 0) return "--";
  return formatDayAmount(value);
}

function formatWorstDay(value: number): string {
  if (value >= 0) return "--";
  return formatDayAmount(value);
}

export function WinRatePanel({ stats }: WinRatePanelProps) {
  const winPct = stats.win_rate * 100;
  const winsLabel = `${stats.winning_trades}W / ${stats.losing_trades}L`;

  const avgDay = formatDayAmount(stats.avg_day);
  const avgTrend =
    stats.avg_day > 0
      ? ("positive" as const)
      : stats.avg_day < 0
        ? ("negative" as const)
        : ("neutral" as const);

  return (
    <div className="flex flex-col gap-4">
      {/* Radial gauge -- the hero element */}
      <div className="bg-white/[0.03] border border-white/[0.08] rounded-lg p-4 flex items-center justify-center">
        <RadialGauge
          value={winPct}
          label="Win Rate"
          sublabel={winsLabel}
          size={140}
          strokeWidth={6}
        />
      </div>

      {/* 2x2 stats grid */}
      <div className="grid grid-cols-2 gap-2">
        <StatCard
          value={String(stats.total_trades)}
          label="Trades"
          trend="neutral"
        />
        <StatCard
          value={formatBestDay(stats.best_day)}
          label="Best Day"
          trend={stats.best_day > 0 ? "positive" : "neutral"}
        />
        <StatCard
          value={formatWorstDay(stats.worst_day)}
          label="Worst Day"
          trend={stats.worst_day < 0 ? "negative" : "neutral"}
        />
        <StatCard value={avgDay} label="Avg Day" trend={avgTrend} />
      </div>
    </div>
  );
}
