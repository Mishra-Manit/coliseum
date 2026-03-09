"use client";

import { SWRConfig } from "swr";
import { TimezoneProvider } from "@/lib/timezone-context";
import { DashboardNavbar } from "@/components/dashboard/dashboard-navbar";
import { useChartData, usePortfolioState } from "@/hooks/use-api";
import { ChartStatCard } from "@/components/chart/chart-stat-card";
import { PortfolioNavChart } from "@/components/chart/portfolio-nav-chart";
import { DailyPnlBars } from "@/components/chart/daily-pnl-bars";
import { WinRatePanel } from "@/components/chart/win-rate-panel";

function ChartContent() {
  const { data: chartData } = useChartData();
  const { data: state } = usePortfolioState();

  const stats = chartData?.stats;
  const daily = chartData?.daily ?? [];
  const currentNav = state?.portfolio?.total_value ?? stats?.current_nav ?? 0;
  const totalPnl = stats?.total_pnl ?? 0;
  const returnPct =
    stats && stats.initial_nav !== 0
      ? ((totalPnl / Math.abs(stats.initial_nav)) * 100).toFixed(1)
      : "0.0";

  return (
    <div className="flex flex-col h-full">
      {/* Page header */}
      <div className="px-6 pt-5 pb-3 flex items-center gap-3 shrink-0 animate-fade-up stagger-1">
        <h1 className="text-[10px] font-mono font-bold text-foreground/70 tracking-[0.2em] uppercase shrink-0">
          Portfolio Performance
        </h1>
        <div className="h-px flex-1 bg-border/50" />
        {chartData && (
          <span className="text-[9px] font-mono text-muted-foreground/40 shrink-0">
            {daily.length} trading day{daily.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Stat cards */}
      <div className="px-6 pb-3 grid grid-cols-2 lg:grid-cols-4 gap-3 shrink-0 animate-fade-up stagger-2">
        <ChartStatCard
          label="Current NAV"
          value={`$${currentNav.toFixed(2)}`}
          trend="neutral"
        />
        <ChartStatCard
          label="Total P&L"
          value={`${totalPnl >= 0 ? "+" : ""}$${Math.abs(totalPnl).toFixed(2)}`}
          trend={totalPnl >= 0 ? "positive" : "negative"}
          subValue={`${totalPnl >= 0 ? "+" : ""}${returnPct}% overall`}
        />
        <ChartStatCard
          label="Win Rate"
          value={stats ? `${(stats.win_rate * 100).toFixed(1)}%` : "—"}
          trend={stats && stats.win_rate >= 0.5 ? "positive" : "negative"}
          subValue={
            stats
              ? `${stats.winning_trades}W / ${stats.losing_trades}L`
              : undefined
          }
        />
        <ChartStatCard
          label="Total Trades"
          value={String(stats?.total_trades ?? 0)}
          trend="neutral"
          subValue={
            stats && stats.total_trades > 0
              ? `Best day +$${stats.best_day.toFixed(2)}`
              : undefined
          }
        />
      </div>

      {/* Main cumulative P&L chart */}
      <div className="flex-1 px-6 pb-3 min-h-0 animate-fade-up stagger-3">
        <div className="h-full bg-card/25 border border-border rounded-lg flex flex-col p-4">
          <div className="flex items-center justify-between mb-3 shrink-0">
            <div className="flex items-baseline gap-2.5">
              <span className="text-[9px] font-mono text-muted-foreground/60 tracking-[0.14em] uppercase">
                Cumulative P&L
              </span>
              {stats && (
                <span
                  className={`text-[13px] font-mono font-semibold tabular-nums ${
                    stats.total_pnl >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {stats.total_pnl >= 0 ? "+" : ""}
                  {stats.total_pnl.toFixed(2)}
                </span>
              )}
            </div>
            <span className="text-[9px] font-mono text-muted-foreground/35 tracking-[0.1em]">
              ALL TIME
            </span>
          </div>
          <div className="flex-1 min-h-0">
            <PortfolioNavChart data={daily} />
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="px-6 pb-5 grid grid-cols-1 lg:grid-cols-3 gap-3 shrink-0 h-52 animate-fade-up stagger-4">
        {/* Daily P&L bars — 2/3 width */}
        <div className="lg:col-span-2 bg-card/25 border border-border rounded-lg flex flex-col p-4">
          <div className="flex items-center justify-between mb-3 shrink-0">
            <span className="text-[9px] font-mono text-muted-foreground/60 tracking-[0.14em] uppercase">
              Daily P&L
            </span>
          </div>
          <div className="flex-1 min-h-0">
            <DailyPnlBars data={daily} />
          </div>
        </div>

        {/* Win / Loss breakdown — 1/3 width */}
        <div className="bg-card/25 border border-border rounded-lg flex flex-col p-4">
          <div className="mb-3 shrink-0">
            <span className="text-[9px] font-mono text-muted-foreground/60 tracking-[0.14em] uppercase">
              Win / Loss
            </span>
          </div>
          <div className="flex-1 min-h-0">
            {stats ? (
              <WinRatePanel stats={stats} />
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-[11px] font-mono text-muted-foreground/40">
                  NO DATA
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChartPage() {
  return (
    <SWRConfig
      value={{
        revalidateOnFocus: true,
        revalidateOnReconnect: true,
        errorRetryCount: 3,
      }}
    >
      <TimezoneProvider>
        <div className="flex flex-col h-screen bg-background tech-grid noise-bg overflow-hidden">
          <DashboardNavbar />
          <main className="flex-1 overflow-hidden">
            <ChartContent />
          </main>
        </div>
      </TimezoneProvider>
    </SWRConfig>
  );
}
