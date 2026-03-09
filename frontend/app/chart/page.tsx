"use client";

import { useState } from "react";
import { DashboardNavbar } from "@/components/dashboard/dashboard-navbar";
import { useChartData, usePortfolioState } from "@/hooks/use-api";
import { LWPortfolioChart } from "@/components/chart/lw-portfolio-chart";
import { WinRatePanel } from "@/components/chart/win-rate-panel";
import type { Interval } from "@/lib/chart-utils";

// ─── Sidebar stat row ──────────────────────────────────────────────────────

interface StatRowProps {
  label: string;
  value: string;
  sub?: string;
  trend?: "positive" | "negative" | "neutral";
}

function StatRow({ label, value, sub, trend = "neutral" }: StatRowProps) {
  const valueClass =
    trend === "positive"
      ? "text-emerald-400"
      : trend === "negative"
        ? "text-red-400"
        : "text-foreground/80";

  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[8px] font-mono text-muted-foreground/50 tracking-[0.13em] uppercase">
        {label}
      </span>
      <span className={`text-[13px] font-mono font-medium tabular-nums ${valueClass}`}>
        {value}
      </span>
      {sub && (
        <span className="text-[9px] font-mono text-muted-foreground/40 tabular-nums">
          {sub}
        </span>
      )}
    </div>
  );
}

// ─── Left sidebar ──────────────────────────────────────────────────────────

function ChartSidebar() {
  const { data: chartData } = useChartData();
  const { data: state } = usePortfolioState();

  const stats = chartData?.stats;
  const currentNav = state?.portfolio?.total_value ?? stats?.current_nav ?? 0;
  const totalPnl = stats?.total_pnl ?? 0;
  const isPositive = totalPnl >= 0;
  const returnPct =
    stats && stats.initial_nav !== 0
      ? ((totalPnl / Math.abs(stats.initial_nav)) * 100).toFixed(1)
      : "0.0";

  return (
    <aside className="w-40 shrink-0 border-r border-border flex flex-col overflow-hidden animate-fade-up stagger-1">
      {/* NAV header */}
      <div className="p-4 border-b border-border shrink-0">
        <p className="text-[8px] font-mono text-muted-foreground/50 tracking-[0.14em] uppercase mb-2">
          Portfolio NAV
        </p>
        <p className="text-[22px] font-mono font-bold text-foreground/90 tabular-nums leading-none">
          ${currentNav.toFixed(2)}
        </p>
        <p
          className={`text-[12px] font-mono font-medium tabular-nums mt-1.5 ${
            isPositive ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {isPositive ? "+" : ""}
          {totalPnl.toFixed(2)}
          <span className="text-[10px] opacity-60 ml-1">
            ({isPositive ? "+" : ""}
            {returnPct}%)
          </span>
        </p>
      </div>

      {/* Stats grid */}
      <div className="flex flex-col gap-4 p-4 overflow-auto flex-1">
        <StatRow
          label="Win Rate"
          value={stats ? `${(stats.win_rate * 100).toFixed(1)}%` : "—"}
          sub={
            stats
              ? `${stats.winning_trades}W / ${stats.losing_trades}L`
              : undefined
          }
          trend={
            stats
              ? stats.win_rate >= 0.5
                ? "positive"
                : "negative"
              : "neutral"
          }
        />
        <StatRow
          label="Total Trades"
          value={String(stats?.total_trades ?? 0)}
          trend="neutral"
        />
        <StatRow
          label="Best Day"
          value={
            stats && stats.best_day > 0
              ? `+$${stats.best_day.toFixed(2)}`
              : "—"
          }
          trend={stats && stats.best_day > 0 ? "positive" : "neutral"}
        />
        <StatRow
          label="Worst Day"
          value={
            stats && stats.worst_day < 0
              ? `$${stats.worst_day.toFixed(2)}`
              : "—"
          }
          trend={stats && stats.worst_day < 0 ? "negative" : "neutral"}
        />

        <div className="h-px bg-border shrink-0" />

        {stats && stats.total_trades > 0 ? (
          <WinRatePanel stats={stats} />
        ) : (
          <div className="flex items-center justify-center py-6">
            <span className="text-[10px] font-mono text-muted-foreground/35 tracking-wider">
              NO DATA
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}

// ─── Main chart area ───────────────────────────────────────────────────────

function ChartMain() {
  const { data: chartData } = useChartData();
  const [interval, setInterval] = useState<Interval>("1D");

  const daily = chartData?.daily ?? [];
  const totalPnl = chartData?.stats?.total_pnl ?? 0;

  return (
    <div className="flex-1 flex flex-col overflow-hidden animate-fade-up stagger-2">
      <LWPortfolioChart
        data={daily}
        interval={interval}
        onIntervalChange={setInterval}
        totalPnl={totalPnl}
      />
    </div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────

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
