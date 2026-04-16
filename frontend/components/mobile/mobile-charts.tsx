"use client";

import { useState } from "react";
import { useChartData } from "@/hooks/use-api";
import { LWPortfolioChart } from "@/components/chart/lw-portfolio-chart";
import { RadialGauge } from "@/components/chart/radial-gauge";
import { StatCard } from "@/components/chart/stat-card";
import { MobileHeader } from "./mobile-header";
import { MobileBottomNav } from "./mobile-bottom-nav";
import type { Interval } from "@/lib/chart-utils";

function formatDayAmount(value: number): string {
  if (value >= 0) return `+$${value.toFixed(2)}`;
  return `-$${Math.abs(value).toFixed(2)}`;
}

export function MobileCharts() {
  const { data: chartData } = useChartData();
  const [interval, setInterval] = useState<Interval>("1D");

  const stats = chartData?.stats;
  const series = chartData?.series ?? [];
  const latestSeriesNav =
    series.length > 0 ? series[series.length - 1].nav : 0;
  const currentNav = latestSeriesNav || stats?.current_nav || 0;
  const totalPnl = stats?.total_pnl ?? 0;
  const isPositive = totalPnl >= 0;
  const initialNav = stats?.initial_nav ?? currentNav - totalPnl;
  const returnPct =
    initialNav !== 0
      ? ((totalPnl / Math.abs(initialNav)) * 100).toFixed(1)
      : "0.0";

  const hasStats = stats && stats.total_trades > 0;
  const winPct = hasStats ? stats.win_rate * 100 : 0;
  const winsLabel = hasStats
    ? `${stats.winning_trades}W / ${stats.losing_trades}L`
    : "";

  return (
    <div className="flex flex-col h-[100dvh] bg-background overflow-hidden">
      <MobileHeader showChartLink={true} />

      <div className="flex-1 flex flex-col overflow-y-auto min-h-0 px-4 py-5 gap-5">
        {/* Portfolio Hero */}
        <div className="rounded-lg bg-white/[0.03] border border-white/[0.08] px-4 py-4 flex flex-col gap-1.5">
          <span className="font-mono text-[11px] font-medium text-muted-foreground/85 tracking-[0.15em]">
            PORTFOLIO NAV
          </span>
          <span className="font-mono text-[32px] font-bold text-foreground/90 tabular-nums leading-none">
            ${currentNav.toFixed(2)}
          </span>
          <span
            className={`font-mono text-[13px] font-medium tabular-nums ${
              isPositive ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {isPositive ? "+" : ""}${totalPnl.toFixed(2)} ({isPositive ? "+" : ""}
            {returnPct}%)
          </span>
        </div>

        {/* Gauge + Stats Row (horizontal, matching design) */}
        {hasStats ? (
          <div className="flex gap-3 w-full">
            {/* Gauge Card */}
            <div className="bg-white/[0.03] border border-white/[0.08] rounded-lg p-4 flex items-center justify-center">
              <RadialGauge
                value={winPct}
                label="Win Rate"
                sublabel={winsLabel}
                size={110}
                strokeWidth={6}
              />
            </div>

            {/* 2x2 Stats Grid */}
            <div className="flex-1 grid grid-cols-2 gap-2">
              <StatCard
                value={String(stats.total_trades)}
                label="Trades"
                trend="neutral"
              />
              <StatCard
                value={
                  stats.best_day > 0
                    ? formatDayAmount(stats.best_day)
                    : "--"
                }
                label="Best Day"
                trend={stats.best_day > 0 ? "positive" : "neutral"}
              />
              <StatCard
                value={
                  stats.worst_day < 0
                    ? formatDayAmount(stats.worst_day)
                    : "--"
                }
                label="Worst Day"
                trend={stats.worst_day < 0 ? "negative" : "neutral"}
              />
              <StatCard
                value={formatDayAmount(stats.avg_day)}
                label="Avg Day"
                trend={
                  stats.avg_day > 0
                    ? "positive"
                    : stats.avg_day < 0
                      ? "negative"
                      : "neutral"
                }
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-12 bg-white/[0.03] border border-white/[0.08] rounded-lg">
            <span className="font-mono text-[11px] text-muted-foreground tracking-wider">
              NO DATA
            </span>
          </div>
        )}

        {/* Chart Section */}
        <div className="rounded-lg bg-white/[0.03] border border-white/[0.08] overflow-hidden">
          <div className="h-[260px]">
            <LWPortfolioChart
              data={series}
              interval={interval}
              onIntervalChange={setInterval}
              currentNav={currentNav}
            />
          </div>
        </div>
      </div>

      <MobileBottomNav />
    </div>
  );
}
