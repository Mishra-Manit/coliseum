"use client";

import { RefreshCw } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useConfig, useDaemonStatus, usePortfolioState } from "@/hooks/use-api";
import { useTimezone, type Timezone } from "@/lib/timezone-context";

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function DashboardNavbar() {
  const { data: config, mutate } = useConfig();
  const { data: daemon } = useDaemonStatus();
  const { data: state } = usePortfolioState();
  const { tz, setTz } = useTimezone();

  const paperMode =
    (config?.trading as Record<string, unknown>)?.paper_mode ?? true;

  const isOnline = daemon?.available ?? false;
  const isPaused = daemon?.paused ?? false;

  const totalValue = state?.portfolio?.total_value ?? 0;
  const cashBalance = state?.portfolio?.cash_balance ?? 0;
  const openCount = state?.open_positions?.length ?? 0;

  return (
    <nav className="sticky top-0 z-50 h-11 border-b border-border bg-card/80 backdrop-blur-xl flex items-center px-5">
      {/* Wordmark */}
      <div className="flex items-center gap-3 shrink-0">
        <span className="font-mono text-xs font-bold text-foreground tracking-[0.2em] uppercase">
          Coliseum
        </span>
        {paperMode ? (
          <Badge
            variant="outline"
            className="border-yellow-600/25 bg-yellow-600/8 text-yellow-500/70 text-[9px] h-[18px] px-1.5 font-mono tracking-wider"
          >
            PAPER
          </Badge>
        ) : (
          <Badge
            variant="outline"
            className="border-emerald-600/25 bg-emerald-600/8 text-emerald-400/70 text-[9px] h-[18px] px-1.5 font-mono tracking-wider"
          >
            LIVE
          </Badge>
        )}
      </div>

      <div className="w-px h-4 bg-border mx-5 shrink-0" />

      {/* Live stat ticker */}
      <div className="flex items-center gap-6 flex-1 min-w-0 overflow-hidden">
        <StatPill label="NAV" value={`$${totalValue.toFixed(2)}`} />
        <StatPill label="CASH" value={`$${cashBalance.toFixed(2)}`} />
        <StatPill
          label="POS"
          value={String(openCount)}
          dimmed={openCount === 0}
        />
        {daemon?.available && (
          <StatPill label="UP" value={formatUptime(daemon.uptime_seconds)} />
        )}
        {daemon?.available && (
          <StatPill label="CYCLES" value={String(daemon.cycles_completed)} />
        )}
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Timezone selector */}
        <TzSelector tz={tz} setTz={setTz} />

        <button
          onClick={() => mutate()}
          className="p-1.5 rounded hover:bg-secondary text-muted-foreground/50 hover:text-muted-foreground transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-3 w-3" />
        </button>

        <div className="flex items-center gap-2 pl-3 border-l border-border">
          <span className="relative flex h-1.5 w-1.5">
            {isOnline && !isPaused && (
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-60" />
            )}
            <span
              className={`relative inline-flex rounded-full h-1.5 w-1.5 ${
                !isOnline
                  ? "bg-zinc-600"
                  : isPaused
                    ? "bg-yellow-500"
                    : "bg-emerald-500"
              }`}
            />
          </span>
          <span className="text-[10px] font-mono text-muted-foreground/60 tracking-wider">
            {!isOnline ? "OFFLINE" : isPaused ? "PAUSED" : "RUNNING"}
          </span>
        </div>
      </div>
    </nav>
  );
}

function TzSelector({
  tz,
  setTz,
}: {
  tz: Timezone;
  setTz: (tz: Timezone) => void;
}) {
  return (
    <div className="flex items-center border border-border rounded overflow-hidden">
      {(["EST", "PST"] as Timezone[]).map((option) => (
        <button
          key={option}
          onClick={() => setTz(option)}
          className={`px-2 py-0.5 text-[9px] font-mono tracking-wider transition-colors ${
            tz === option
              ? "bg-primary/15 text-primary border-r border-border last:border-r-0"
              : "text-muted-foreground/40 hover:text-muted-foreground/70 border-r border-border last:border-r-0"
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  );
}

function StatPill({
  label,
  value,
  dimmed = false,
}: {
  label: string;
  value: string;
  dimmed?: boolean;
}) {
  return (
    <div className="flex items-baseline gap-1.5 shrink-0">
      <span className="text-[9px] font-mono text-muted-foreground/40 tracking-[0.12em] uppercase">
        {label}
      </span>
      <span
        className={`text-[11px] font-mono font-medium tabular-nums ${
          dimmed ? "text-muted-foreground/30" : "text-foreground/80"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
