"use client";

import type { ChartStats } from "@/lib/types";

interface WinRatePanelProps {
  stats: ChartStats;
}

export function WinRatePanel({ stats }: WinRatePanelProps) {
  const winPct = Math.round(stats.win_rate * 100);
  const lossPct = 100 - winPct;

  return (
    <div className="flex flex-col gap-2">
      <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-3 flex flex-col gap-1">
        <span className="text-[8px] font-mono text-muted-foreground/70 tracking-[0.12em] uppercase">
          Wins
        </span>
        <span className="text-[22px] font-mono font-bold text-emerald-400 tabular-nums leading-none">
          {stats.winning_trades}
        </span>
        <span className="text-[10px] font-mono text-emerald-400/70 tabular-nums">
          {winPct}%
        </span>
      </div>
      <div className="bg-red-500/5 border border-red-500/10 rounded-lg p-3 flex flex-col gap-1">
        <span className="text-[8px] font-mono text-muted-foreground/70 tracking-[0.12em] uppercase">
          Losses
        </span>
        <span className="text-[22px] font-mono font-bold text-red-400 tabular-nums leading-none">
          {stats.losing_trades}
        </span>
        <span className="text-[10px] font-mono text-red-400/70 tabular-nums">
          {lossPct}%
        </span>
      </div>
    </div>
  );
}
