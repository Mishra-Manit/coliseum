"use client";

import { format, parseISO, isValid } from "date-fns";
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  CircleDot,
  Receipt,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useLedger, usePortfolioState } from "@/hooks/use-api";
import type { LedgerEntry, Position } from "@/lib/types";

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
      {/* Top half — Positions */}
      <div className="flex flex-col h-1/2 border-b border-border overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 shrink-0 border-b border-border">
          <span className="text-[9px] font-mono text-muted-foreground/40 tracking-[0.15em] uppercase">
            Positions
          </span>
          <span className="text-[9px] font-mono text-muted-foreground/30 tabular-nums">
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

      {/* Bottom half — Ledger */}
      <div className="flex flex-col h-1/2 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2.5 shrink-0 border-b border-border">
          <span className="text-[9px] font-mono text-muted-foreground/40 tracking-[0.15em] uppercase">
            Ledger
          </span>
          <div className="flex items-center gap-3">
            {winRate !== null && (
              <span
                className={`text-[9px] font-mono tabular-nums ${
                  winRate >= 60
                    ? "text-emerald-400/70"
                    : winRate >= 40
                      ? "text-amber-400/70"
                      : "text-red-400/70"
                }`}
              >
                {winRate}% win
              </span>
            )}
            <span className="text-[9px] font-mono text-muted-foreground/30 tabular-nums">
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
  positions: Position[];
  isLoading: boolean;
  onSelectOpportunity?: (id: string) => void;
}) {
  if (isLoading) {
    return (
      <div className="p-4 space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="shimmer h-10 rounded" />
        ))}
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground/30 gap-2">
        <CircleDot className="h-6 w-6" />
        <p className="text-[11px] font-mono tracking-wider">NO POSITIONS</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto min-h-0">
      <Table>
        <TableHeader>
          <TableRow className="border-border hover:bg-transparent">
            <TableHead className="text-[9px] text-muted-foreground/40 font-mono h-8 uppercase tracking-wider w-full px-4">
              Market
            </TableHead>
            <TableHead className="text-[9px] text-muted-foreground/40 font-mono h-8 uppercase tracking-wider whitespace-nowrap px-2">
              Side
            </TableHead>
            <TableHead className="text-[9px] text-muted-foreground/40 font-mono h-8 text-right uppercase tracking-wider whitespace-nowrap px-2">
              Qty
            </TableHead>
            <TableHead className="text-[9px] text-muted-foreground/40 font-mono h-8 text-right uppercase tracking-wider whitespace-nowrap px-4">
              Entry
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {positions.map((pos) => {
            const isClickable = !!pos.opportunity_id && !!onSelectOpportunity;
            return (
              <TableRow
                key={pos.id}
                onClick={
                  isClickable
                    ? () => onSelectOpportunity!(pos.opportunity_id!)
                    : undefined
                }
                className={`border-border/50 transition-colors ${
                  isClickable
                    ? "cursor-pointer hover:bg-amber-500/4"
                    : "hover:bg-secondary/20"
                }`}
              >
                <TableCell className="text-[11px] text-foreground/80 font-mono py-2 max-w-0 w-full px-4">
                  <span className="block truncate" title={pos.market_ticker}>
                    {pos.market_ticker}
                  </span>
                </TableCell>
                <TableCell className="py-2 px-2">
                  <span
                    className={`text-[10px] font-mono font-semibold ${
                      pos.side === "YES"
                        ? "text-emerald-400"
                        : pos.side === "NO"
                          ? "text-red-400"
                          : "text-muted-foreground"
                    }`}
                  >
                    {pos.side}
                  </span>
                </TableCell>
                <TableCell className="text-[11px] text-foreground/70 text-right py-2 font-mono tabular-nums px-2">
                  {pos.contracts}
                </TableCell>
                <TableCell className="text-[11px] text-foreground/70 text-right py-2 font-mono tabular-nums px-4">
                  {Math.round(pos.average_entry * 100)}c
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
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
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground/30 gap-2">
        <Receipt className="h-6 w-6" />
        <p className="text-[11px] font-mono tracking-wider">NO TRADES</p>
      </div>
    );
  }

  const grouped = groupByDate(entries);

  return (
    <div className="h-full overflow-y-auto min-h-0">
      <div className="px-4 py-3 space-y-4">
        {grouped.map(([dateLabel, dayEntries]) => (
          <div key={dateLabel}>
            <p className="text-[9px] font-mono text-muted-foreground/30 uppercase tracking-[0.15em] mb-2">
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
      onClick={
        isClickable
          ? () => onSelectOpportunity!(entry.opportunity_id!)
          : undefined
      }
      disabled={!isClickable}
      className={`w-full text-left flex items-center gap-2.5 px-2 py-1.5 rounded transition-colors ${
        isClickable
          ? "hover:bg-amber-500/4 cursor-pointer"
          : "cursor-default"
      }`}
    >
      {/* Type indicator */}
      <div
        className={`shrink-0 w-1 h-5 rounded-full ${
          isBuy
            ? "bg-sky-500/50"
            : pnl > 0
              ? "bg-emerald-500/50"
              : pnl < 0
                ? "bg-red-500/50"
                : "bg-border"
        }`}
      />

      {/* Icon */}
      <div
        className={`shrink-0 ${
          isBuy
            ? "text-sky-500/60"
            : pnl >= 0
              ? "text-emerald-500/60"
              : "text-red-500/60"
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
          className="text-[10px] font-mono text-foreground/70 truncate leading-tight"
          title={entry.market_ticker}
        >
          {entry.market_ticker}
        </p>
        <div className="flex items-center gap-1 mt-0.5">
          <span
            className={`text-[9px] font-mono ${
              entry.side === "YES"
                ? "text-emerald-400/60"
                : "text-red-400/60"
            }`}
          >
            {entry.side}
          </span>
          <span className="text-[9px] text-muted-foreground/30 font-mono">
            ×{entry.contracts}
          </span>
        </div>
      </div>

      {/* Right: price/pnl + time */}
      <div className="shrink-0 text-right">
        {isBuy ? (
          <p className="text-[10px] font-mono text-foreground/60 tabular-nums">
            {Math.round(entry.price * 100)}c
          </p>
        ) : (
          <p
            className={`text-[10px] font-mono font-semibold tabular-nums ${
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
        <p className="text-[9px] text-muted-foreground/30 font-mono mt-0.5 tabular-nums">
          {formatTime(entry.timestamp)}
        </p>
      </div>
    </button>
  );
}
