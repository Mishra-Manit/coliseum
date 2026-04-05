"use client";

import { format, parseISO, isValid } from "date-fns";
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  CircleDot,
  Receipt,
} from "lucide-react";
import { useLedger, usePortfolioState } from "@/hooks/use-api";
import type { EnrichedPosition, LedgerEntry } from "@/lib/types";
import { FontSize } from "@/lib/typography";
import { Muted, Base, BgTint, BorderTint } from "@/lib/styles";

interface PositionsLedgerPanelProps {
  onSelectOpportunity?: (id: string) => void;
}

export function PositionsLedgerPanel({
  onSelectOpportunity,
}: PositionsLedgerPanelProps) {
  const { data: state, isLoading: stateLoading } = usePortfolioState();
  const { data: entries, isLoading: ledgerLoading } = useLedger(150);

  const positions = state?.open_positions ?? [];
  const allEntries = entries ?? [];
  const closes = allEntries.filter((e) => e.type === "close" && e.pnl != null);
  const wins = closes.filter((e) => (e.pnl ?? 0) > 0).length;
  const winRate =
    closes.length > 0 ? Math.round((wins / closes.length) * 100) : null;

  return (
    <div className="flex flex-col h-full">
      {/* Top — Positions (35%) */}
      <div className="flex flex-col border-b border-border overflow-hidden" style={{ height: "35%" }}>
        <div className="flex items-center justify-between px-4 py-2.5 shrink-0 border-b border-border">
          <span className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-[0.15em] uppercase`}>
            Positions
          </span>
          <span className={`${FontSize.small} font-mono ${Muted.mutedText} tabular-nums`}>
            {positions.length}
          </span>
        </div>
        <div className="flex-1 overflow-hidden">
          <PositionsContent
            positions={positions}
            isLoading={stateLoading}
            onSelectOpportunity={onSelectOpportunity}
          />
        </div>
      </div>

      {/* Bottom — Ledger (65%) */}
      <div className="flex flex-col overflow-hidden" style={{ height: "65%" }}>
        <div className="flex items-center justify-between px-4 py-2.5 shrink-0 border-b border-border">
          <span className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-[0.15em] uppercase`}>
            Ledger
          </span>
          <div className="flex items-center gap-3">
            {winRate !== null && (
              <span
                className={`${FontSize.small} font-mono tabular-nums ${
                  winRate >= 60
                    ? Muted.emeraldLabel
                    : winRate >= 40
                      ? Muted.amberWinRate
                      : Muted.redLabel
                }`}
              >
                {winRate}% win
              </span>
            )}
            <span className={`${FontSize.small} font-mono ${Muted.mutedText} tabular-nums`}>
              {allEntries.length}
            </span>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          <LedgerContent
            entries={allEntries}
            isLoading={ledgerLoading}
            onSelectOpportunity={onSelectOpportunity}
          />
        </div>
      </div>
    </div>
  );
}

function PositionsContent({
  positions,
  isLoading,
  onSelectOpportunity,
}: {
  positions: EnrichedPosition[];
  isLoading: boolean;
  onSelectOpportunity?: (id: string) => void;
}) {
  if (isLoading) {
    return (
      <div className="p-4 space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="shimmer h-12 rounded" />
        ))}
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${Muted.mutedText} gap-2`}>
        <CircleDot className="h-6 w-6" />
        <p className={`${FontSize.medium} font-mono tracking-wider`}>NO POSITIONS</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto min-h-0 px-3 py-2 space-y-1">
      {positions.map((pos) => {
        const isClickable = !!pos.opportunity_id && !!onSelectOpportunity;
        const entryC = Math.round(pos.average_entry * 100);
        const nowC = pos.current_price > 0 ? Math.round(pos.current_price * 100) : null;

        return (
          <button
            key={pos.id}
            onClick={isClickable ? () => onSelectOpportunity!(pos.opportunity_id!) : undefined}
            disabled={!isClickable}
            className={`w-full text-left px-3 py-2 rounded transition-colors ${
              isClickable
                ? `cursor-pointer ${BgTint.amberRowHoverState}`
                : "cursor-default hover:bg-secondary/20"
            }`}
          >
            {/* Line 1: ticker + side x qty + P&L */}
            <div className="flex items-center gap-2">
              <span
                className={`${FontSize.medium} font-mono ${Base.foreground} truncate flex-1 min-w-0`}
                title={pos.market_ticker}
              >
                {pos.market_ticker}
              </span>
              <span
                className={`${FontSize.small} font-mono font-semibold shrink-0 ${
                  pos.side === "YES" ? "text-emerald-400"
                    : pos.side === "NO" ? "text-red-400"
                    : "text-muted-foreground"
                }`}
              >
                {pos.side}
              </span>
              <span className={`${FontSize.small} ${Muted.mutedText} font-mono shrink-0`}>
                x{pos.contracts}
              </span>
              <span
                className={`${FontSize.medium} font-mono font-semibold tabular-nums shrink-0 ml-auto ${
                  pos.unrealized_pnl >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {pos.unrealized_pnl >= 0 ? "+" : ""}${pos.unrealized_pnl.toFixed(2)}
              </span>
            </div>
            {/* Line 2: price movement + pct change */}
            <div className="flex items-center mt-0.5">
              <span className={`${FontSize.small} font-mono ${Muted.mutedText} tabular-nums`}>
                {entryC}c{nowC !== null ? ` \u2192 ${nowC}c` : ""}
              </span>
              <span
                className={`${FontSize.small} font-mono tabular-nums ml-auto ${
                  pos.pct_change >= 0 ? Muted.emeraldLabel : Muted.redLabel
                }`}
              >
                {pos.pct_change >= 0 ? "+" : ""}{pos.pct_change.toFixed(1)}%
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

function groupByDate(entries: LedgerEntry[]): [string, LedgerEntry[]][] {
  const map = new Map<string, LedgerEntry[]>();
  for (const entry of entries) {
    let dateKey = "Unknown";
    try {
      const d = parseISO(entry.timestamp);
      if (isValid(d)) dateKey = format(d, "MMM d");
    } catch {
      // keep Unknown
    }
    const existing = map.get(dateKey) ?? [];
    map.set(dateKey, [...existing, entry]);
  }
  return Array.from(map.entries());
}

function formatTime(ts: string): string {
  try {
    const d = parseISO(ts);
    return isValid(d) ? format(d, "HH:mm") : "--:--";
  } catch {
    return "--:--";
  }
}

function LedgerContent({
  entries,
  isLoading,
  onSelectOpportunity,
}: {
  entries: LedgerEntry[];
  isLoading: boolean;
  onSelectOpportunity?: (id: string) => void;
}) {
  if (isLoading) {
    return (
      <div className="p-4 space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="shimmer h-9 rounded" />
        ))}
      </div>
    );
  }

  if (entries.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${Muted.mutedText} gap-2`}>
        <Receipt className="h-6 w-6" />
        <p className={`${FontSize.medium} font-mono tracking-wider`}>NO TRADES</p>
      </div>
    );
  }

  const grouped = groupByDate(entries);

  return (
    <div className="h-full overflow-y-auto min-h-0">
      <div className="px-4 py-3 space-y-4">
        {grouped.map(([dateLabel, dayEntries]) => (
          <div key={dateLabel}>
            <p className={`${FontSize.small} font-mono ${Muted.mutedText} uppercase tracking-[0.15em] mb-2`}>
              {dateLabel}
            </p>
            <div className="space-y-0.5">
              {dayEntries.map((entry) => (
                <LedgerRow
                  key={entry.id}
                  entry={entry}
                  onSelectOpportunity={onSelectOpportunity}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LedgerRow({
  entry,
  onSelectOpportunity,
}: {
  entry: LedgerEntry;
  onSelectOpportunity?: (id: string) => void;
}) {
  const isClickable = !!entry.opportunity_id && !!onSelectOpportunity;
  const isBuy = entry.type === "buy";
  const pnl = entry.pnl ?? 0;

  return (
    <button
      onClick={isClickable ? () => onSelectOpportunity!(entry.opportunity_id!) : undefined}
      disabled={!isClickable}
      className={`w-full text-left flex items-center gap-2.5 px-2 py-1.5 rounded transition-colors ${
        isClickable
          ? `${BgTint.amberRowHoverState} cursor-pointer`
          : "cursor-default"
      }`}
    >
      {/* Type indicator */}
      <div
        className={`shrink-0 w-1 h-5 rounded-full ${
          isBuy
            ? BgTint.buyBar
            : pnl > 0
              ? BgTint.winBar
              : pnl < 0
                ? BgTint.lossBar
                : "bg-border"
        }`}
      />

      {/* Icon */}
      <div
        className={`shrink-0 ${
          isBuy
            ? Muted.skyIcon
            : pnl >= 0
              ? Muted.emeraldIcon
              : Muted.redIcon
        }`}
      >
        {isBuy ? (
          <ArrowDownToLine className="h-3 w-3" />
        ) : (
          <ArrowUpFromLine className="h-3 w-3" />
        )}
      </div>

      {/* Ticker + side */}
      <div className="flex-1 min-w-0">
        <p
          className={`${FontSize.medium} font-mono ${Muted.foreground} truncate leading-tight`}
          title={entry.market_ticker}
        >
          {entry.market_ticker}
        </p>
        <div className="flex items-center gap-1 mt-0.5">
          <span
            className={`${FontSize.small} font-mono ${
              entry.side === "YES" ? Muted.emeraldLabel : Muted.redLabel
            }`}
          >
            {entry.side}
          </span>
          <span className={`${FontSize.small} ${Muted.mutedText} font-mono`}>
            ×{entry.contracts}
          </span>
        </div>
      </div>

      {/* Right: price/pnl + time */}
      <div className="shrink-0 text-right">
        {isBuy ? (
          <p className={`${FontSize.medium} font-mono ${Muted.foreground} tabular-nums`}>
            {Math.round(entry.price * 100)}c
          </p>
        ) : (
          <p
            className={`${FontSize.medium} font-mono font-semibold tabular-nums ${
              pnl > 0
                ? "text-emerald-400"
                : pnl < 0
                  ? "text-red-400"
                  : "text-muted-foreground"
            }`}
          >
            {pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
          </p>
        )}
        <p className={`${FontSize.small} ${Muted.mutedText} font-mono mt-0.5 tabular-nums`}>
          {formatTime(entry.timestamp)}
        </p>
      </div>
    </button>
  );
}
