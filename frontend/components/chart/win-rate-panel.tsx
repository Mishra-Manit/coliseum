"use client";

import type { ChartStats } from "@/lib/types";

interface WinRatePanelProps {
  stats: ChartStats;
}

export function WinRatePanel({ stats }: WinRatePanelProps) {
  const winPct = Math.round(stats.win_rate * 100);
  const lossPct = 100 - winPct;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-3">
        <div className="flex-1 bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-3 flex flex-col gap-1">
          <span className="text-[8px] font-mono text-muted-foreground/60 tracking-[0.12em] uppercase">
            Wins
          </span>
          <span className="text-[22px] font-mono font-bold text-emerald-400 tabular-nums leading-none">
            {stats.winning_trades}
          </span>
          <span className="text-[10px] font-mono text-emerald-400/50 tabular-nums">
            {winPct}%
          </span>
        </div>
        <div className="flex-1 bg-red-500/5 border border-red-500/10 rounded-lg p-3 flex flex-col gap-1">
          <span className="text-[8px] font-mono text-muted-foreground/60 tracking-[0.12em] uppercase">
            Losses
          </span>
          <span className="text-[22px] font-mono font-bold text-red-400 tabular-nums leading-none">
            {stats.losing_trades}
          </span>
          <span className="text-[10px] font-mono text-red-400/50 tabular-nums">
            {lossPct}%
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="h-1 rounded-full bg-border/50 overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-emerald-700 to-emerald-400 transition-all duration-700"
            style={{ width: `${winPct}%` }}
          />
        </div>
        <div className="flex justify-between">
          <span className="text-[9px] font-mono text-muted-foreground/40">
            Best&nbsp;
            <span className="text-emerald-400/60">
              {stats.best_day >= 0 ? "+" : ""}
              {stats.best_day.toFixed(2)}
            </span>
          </span>
          <span className="text-[9px] font-mono text-muted-foreground/40">
            Worst&nbsp;
            <span className="text-red-400/60">{stats.worst_day.toFixed(2)}</span>
          </span>
        </div>
      </div>
    </div>
  );
}
