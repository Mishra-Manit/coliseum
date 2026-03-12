"use client";

import type { ChartStats } from "@/lib/types";
import { FontSize } from "@/lib/typography";
import { O70, BgTint, BorderTint } from "@/lib/styles";

interface WinRatePanelProps {
  stats: ChartStats;
}

export function WinRatePanel({ stats }: WinRatePanelProps) {
  const winPct = Math.round(stats.win_rate * 100);
  const lossPct = 100 - winPct;

  return (
    <div className="flex flex-col gap-2">
      <div className={`${BgTint.emeraldBox} border ${BorderTint.winPanel} rounded-lg p-3 flex flex-col gap-1`}>
        <span className={`${FontSize.small} font-mono ${O70.mutedText} tracking-[0.12em] uppercase`}>
          Wins
        </span>
        <span className="text-[22px] font-mono font-bold text-emerald-400 tabular-nums leading-none">
          {stats.winning_trades}
        </span>
        <span className={`${FontSize.small} font-mono ${O70.emeraldLabel} tabular-nums`}>
          {winPct}%
        </span>
      </div>
      <div className={`${BgTint.redBox} border ${BorderTint.lossPanel} rounded-lg p-3 flex flex-col gap-1`}>
        <span className={`${FontSize.small} font-mono ${O70.mutedText} tracking-[0.12em] uppercase`}>
          Losses
        </span>
        <span className="text-[22px] font-mono font-bold text-red-400 tabular-nums leading-none">
          {stats.losing_trades}
        </span>
        <span className={`${FontSize.small} font-mono ${O70.redLabel} tabular-nums`}>
          {lossPct}%
        </span>
      </div>
    </div>
  );
}
