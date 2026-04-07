"use client";

import { useState } from "react";
import { DashboardNavbar } from "@/components/dashboard/dashboard-navbar";
import { useChartData } from "@/hooks/use-api";
import { LWPortfolioChart } from "@/components/chart/lw-portfolio-chart";
import { WinRatePanel } from "@/components/chart/win-rate-panel";
import type { Interval } from "@/lib/chart-utils";
import { FontSize } from "@/lib/typography";
import { Muted, Strong, Faint } from "@/lib/styles";

function ChartSidebar() {
  const { data: chartData } = useChartData();

  const stats = chartData?.stats;
  const series = chartData?.series ?? [];
  const latestSeriesNav = series.length > 0 ? series[series.length - 1].nav : 0;
  const currentNav = latestSeriesNav || stats?.current_nav || 0;
  const totalPnl = stats?.total_pnl ?? 0;
  const isPositive = totalPnl >= 0;
  const initialNav = stats?.initial_nav ?? currentNav - totalPnl;
  const returnPct =
    initialNav !== 0
      ? ((totalPnl / Math.abs(initialNav)) * 100).toFixed(1)
      : "0.0";

  return (
    <aside className="w-[220px] shrink-0 border-r border-border flex flex-col overflow-hidden animate-fade-up stagger-1">
      {/* NAV header */}
      <div className="p-4 border-b border-border shrink-0">
        <p
          className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-[0.14em] uppercase mb-2`}
        >
          Portfolio NAV
        </p>
        <p
          className={`text-[26px] font-mono font-bold ${Strong.foreground} tabular-nums leading-none`}
        >
          ${currentNav.toFixed(2)}
        </p>
        <p
          className={`text-[12px] font-mono font-medium tabular-nums mt-2 ${
            isPositive ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {isPositive ? "+" : ""}
          {totalPnl.toFixed(2)}
          <span className={`${FontSize.small} ${Faint.opacityClass} ml-1`}>
            ({isPositive ? "+" : ""}
            {returnPct}%)
          </span>
        </p>
      </div>

      {/* Radial HUD + Stats */}
      <div className="flex flex-col gap-4 p-4 overflow-auto flex-1">
        {stats && stats.total_trades > 0 ? (
          <WinRatePanel stats={stats} />
        ) : (
          <div className="flex items-center justify-center py-12">
            <span
              className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-wider`}
            >
              NO DATA
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}

function ChartMain() {
  const { data: chartData } = useChartData();
  const [interval, setInterval] = useState<Interval>("1D");

  const series = chartData?.series ?? [];
  const stats = chartData?.stats;
  const latestSeriesNav = series.length > 0 ? series[series.length - 1].nav : 0;
  const currentNav = latestSeriesNav || stats?.current_nav || 0;

  return (
    <div className="flex-1 flex flex-col overflow-hidden animate-fade-up stagger-2">
      <LWPortfolioChart
        data={series}
        interval={interval}
        onIntervalChange={setInterval}
        currentNav={currentNav}
      />
    </div>
  );
}

export default function ChartPage() {
  return (
    <div className="flex flex-col h-screen bg-background tech-grid noise-bg overflow-hidden">
      <DashboardNavbar />
      <main className="flex-1 overflow-hidden flex min-h-0">
        <ChartSidebar />
        <ChartMain />
      </main>
    </div>
  );
}
