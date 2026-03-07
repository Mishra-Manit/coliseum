"use client";

import { format, parseISO, isValid } from "date-fns";
import { ArrowDownToLine, ArrowUpFromLine, Receipt } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useLedger } from "@/hooks/use-api";
import type { LedgerEntry } from "@/lib/types";

function groupByDate(entries: LedgerEntry[]): [string, LedgerEntry[]][] {
  const map = new Map<string, LedgerEntry[]>();
  for (const entry of entries) {
    let dateKey = "Unknown";
    try {
      const d = parseISO(entry.timestamp);
      if (isValid(d)) dateKey = format(d, "MMM d, yyyy");
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

function pnlColor(pnl: number): string {
  if (pnl > 0) return "text-emerald-400";
  if (pnl < 0) return "text-red-400";
  return "text-muted-foreground";
}

function pnlLabel(pnl: number): string {
  const sign = pnl >= 0 ? "+" : "";
  return `${sign}$${pnl.toFixed(2)}`;
}

interface TradeLedgerProps {
  onSelectOpportunity?: (id: string) => void;
}

export function TradeLedger({ onSelectOpportunity }: TradeLedgerProps) {
  const { data: entries, isLoading } = useLedger(150);

  const allEntries = entries ?? [];
  const closes = allEntries.filter((e) => e.type === "close" && e.pnl != null);
  const wins = closes.filter((e) => (e.pnl ?? 0) > 0).length;
  const winRate =
    closes.length > 0 ? Math.round((wins / closes.length) * 100) : null;

  const grouped = groupByDate(allEntries);

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="font-display text-lg font-semibold text-foreground">
            Trade Ledger
          </CardTitle>
          <div className="flex items-center gap-1.5">
            {winRate !== null && (
              <Badge
                variant="outline"
                className={`text-[10px] font-mono border ${
                  winRate >= 60
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                    : winRate >= 40
                    ? "border-amber-500/30 bg-amber-500/10 text-amber-400"
                    : "border-red-500/30 bg-red-500/10 text-red-400"
                }`}
              >
                {winRate}% win
              </Badge>
            )}
            <Badge
              variant="outline"
              className="border-border bg-secondary/50 text-muted-foreground text-[10px] font-mono"
            >
              {allEntries.length} entries
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full bg-secondary rounded-lg" />
            ))}
          </div>
        ) : allEntries.length === 0 ? (
          <div className="text-center py-10 text-muted-foreground">
            <Receipt className="h-7 w-7 mx-auto mb-2 opacity-20" />
            <p className="text-xs font-medium">No trades recorded yet</p>
          </div>
        ) : (
          <ScrollArea className="h-[340px] pr-1">
            <div className="space-y-4">
              {grouped.map(([dateLabel, dayEntries]) => (
                <div key={dateLabel}>
                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-widest mb-1.5 px-0.5">
                    {dateLabel}
                  </p>
                  <div className="space-y-1">
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
          </ScrollArea>
        )}
      </CardContent>
    </Card>
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

  return (
    <button
      onClick={
        isClickable
          ? () => onSelectOpportunity!(entry.opportunity_id!)
          : undefined
      }
      disabled={!isClickable}
      className={`w-full text-left flex items-center gap-2.5 px-2.5 py-2 rounded-lg border transition-all duration-150 ${
        isClickable
          ? "border-transparent hover:border-amber-600/20 hover:bg-amber-500/5 cursor-pointer"
          : "border-transparent cursor-default"
      }`}
    >
      {/* Icon */}
      <div
        className={`shrink-0 p-1.5 rounded-md ${
          isBuy
            ? "bg-sky-500/10 text-sky-400"
            : (entry.pnl ?? 0) >= 0
            ? "bg-emerald-500/10 text-emerald-400"
            : "bg-red-500/10 text-red-400"
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
          className="text-[11px] font-mono text-foreground truncate leading-tight"
          title={entry.market_ticker}
        >
          {entry.market_ticker}
        </p>
        <div className="flex items-center gap-1.5 mt-0.5">
          <span className="text-[10px] text-muted-foreground font-mono">
            {isBuy ? "BUY" : "CLOSE"}
          </span>
          <span
            className={`text-[10px] font-semibold font-mono ${
              entry.side === "YES" ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {entry.side}
          </span>
          <span className="text-[10px] text-muted-foreground font-mono">
            ×{entry.contracts}
          </span>
        </div>
      </div>

      {/* Right side: price / pnl + time */}
      <div className="shrink-0 text-right">
        {isBuy ? (
          <p className="text-[11px] font-mono text-foreground">
            {Math.round(entry.price * 100)}c
          </p>
        ) : (
          <p
            className={`text-[11px] font-mono font-semibold ${pnlColor(entry.pnl ?? 0)}`}
          >
            {pnlLabel(entry.pnl ?? 0)}
          </p>
        )}
        <p className="text-[10px] text-muted-foreground font-mono mt-0.5">
          {formatTime(entry.timestamp)}
        </p>
      </div>
    </button>
  );
}
