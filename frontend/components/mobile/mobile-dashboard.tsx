"use client";

import { useState } from "react";
import { format, parseISO, isValid, formatDistanceToNow } from "date-fns";
import {
  CircleDot,
  Receipt,
  FileText,
  ChevronRight,
  ArrowDownToLine,
  ArrowUpFromLine,
} from "lucide-react";
import { usePortfolioState, useLedger, useOpportunities } from "@/hooks/use-api";
import type { EnrichedPosition, LedgerEntry, OpportunitySummary } from "@/lib/types";
import { MobileHeader } from "./mobile-header";
import { MobileBottomNav } from "./mobile-bottom-nav";
import { MobilePositionDetail } from "./mobile-position-detail";
import { FontSize } from "@/lib/typography";
import { Muted, Base, Soft, Strong, BgTint, BorderTint } from "@/lib/styles";

type Tab = "positions" | "opportunities" | "ledger";

export function MobileDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>("positions");
  const [selectedOpportunityId, setSelectedOpportunityId] = useState<string | null>(null);

  if (selectedOpportunityId) {
    return (
      <MobilePositionDetail
        opportunityId={selectedOpportunityId}
        onBack={() => setSelectedOpportunityId(null)}
      />
    );
  }

  return (
    <div className="flex flex-col h-[100dvh] bg-background overflow-hidden">
      <MobileHeader showChartLink={false} />

      <div className="flex-1 flex flex-col overflow-y-auto min-h-0 px-4 py-4 gap-4">
        {/* Stats strip */}
        <StatsStrip />

        {/* Tab control */}
        <TabControl activeTab={activeTab} onTabChange={setActiveTab} />

        {/* Tab content */}
        {activeTab === "positions" && (
          <>
            <PositionsSection onSelectOpportunity={setSelectedOpportunityId} />
            <LedgerSection onSelectOpportunity={setSelectedOpportunityId} />
          </>
        )}
        {activeTab === "opportunities" && (
          <OpportunitiesSection onSelectOpportunity={setSelectedOpportunityId} />
        )}
        {activeTab === "ledger" && (
          <LedgerSection onSelectOpportunity={setSelectedOpportunityId} />
        )}
      </div>

      <MobileBottomNav />
    </div>
  );
}

function StatsStrip() {
  const { data: portfolio } = usePortfolioState();

  const totalValue = portfolio?.portfolio?.total_value ?? 0;
  const cashBalance = portfolio?.portfolio?.cash_balance ?? 0;
  const openCount = portfolio?.open_positions?.length ?? 0;

  return (
    <div className="flex gap-2 w-full">
      <StatPill label="NAV" value={`$${totalValue.toFixed(2)}`} />
      <StatPill label="CASH" value={`$${cashBalance.toFixed(2)}`} />
      <StatPill label="POS" value={String(openCount)} />
    </div>
  );
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex-1 flex flex-col gap-1 rounded-lg bg-card border border-white/[0.08] px-3 py-2.5">
      <span className="font-mono text-[10px] font-medium text-muted-foreground tracking-[0.1em]">
        {label}
      </span>
      <span className="font-mono text-[15px] font-semibold text-foreground tabular-nums">
        {value}
      </span>
    </div>
  );
}

function TabControl({
  activeTab,
  onTabChange,
}: {
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}) {
  const tabs: { key: Tab; label: string }[] = [
    { key: "positions", label: "Positions" },
    { key: "opportunities", label: "Opportunities" },
    { key: "ledger", label: "Ledger" },
  ];

  return (
    <div className="flex gap-0.5 w-full rounded-lg bg-card border border-white/[0.08] p-[3px]">
      {tabs.map(({ key, label }) => {
        const isActive = activeTab === key;
        return (
          <button
            key={key}
            onClick={() => onTabChange(key)}
            className={`flex-1 flex items-center justify-center rounded-md py-2 transition-colors ${
              isActive
                ? "bg-primary/15 border border-primary/30"
                : "border border-transparent"
            }`}
          >
            <span
              className={`font-mono text-[11px] tracking-wider ${
                isActive
                  ? "font-semibold text-primary"
                  : "font-medium text-muted-foreground/80"
              }`}
            >
              {label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function PositionsSection({
  onSelectOpportunity,
}: {
  onSelectOpportunity: (id: string) => void;
}) {
  const { data: state, isLoading } = usePortfolioState();
  const positions = state?.open_positions ?? [];

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="shimmer h-[60px] rounded-lg" />
        ))}
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-2">
        <CircleDot className="h-6 w-6" />
        <p className={`${FontSize.medium} font-mono tracking-wider`}>NO POSITIONS</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {positions.map((pos) => (
        <PositionCard
          key={pos.id}
          position={pos}
          onSelect={() => pos.opportunity_id && onSelectOpportunity(pos.opportunity_id)}
        />
      ))}
    </div>
  );
}

function PositionCard({
  position,
  onSelect,
}: {
  position: EnrichedPosition;
  onSelect: () => void;
}) {
  const entryC = Math.round(position.average_entry * 100);
  const nowC = position.current_price > 0 ? Math.round(position.current_price * 100) : null;
  const isPositive = position.unrealized_pnl >= 0;

  return (
    <button
      onClick={onSelect}
      className="w-full text-left rounded-lg bg-card border border-white/[0.08] px-3.5 py-3 flex flex-col gap-1.5"
    >
      {/* Row 1: ticker + YES/NO badge + pnl */}
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className={`${FontSize.medium} font-mono text-foreground truncate`}>
            {position.market_ticker}
          </span>
          <span
            className={`shrink-0 font-mono text-[10px] font-semibold px-1.5 py-px rounded ${
              position.side === "YES"
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                : "bg-red-500/10 text-red-400 border border-red-500/30"
            }`}
          >
            {position.side}
          </span>
        </div>
        <span
          className={`font-mono text-xs font-semibold tabular-nums shrink-0 ${
            isPositive ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {isPositive ? "+" : ""}${position.unrealized_pnl.toFixed(2)}
        </span>
      </div>
      {/* Row 2: price movement + pct */}
      <div className="flex items-center justify-between w-full">
        <span className="font-mono text-[10px] text-muted-foreground tabular-nums">
          {entryC}c {nowC !== null ? <>&nbsp;&gt;&nbsp;{nowC}c</> : null} &nbsp;&middot;&nbsp;x{position.contracts}
        </span>
        <span
          className={`font-mono text-[11px] font-medium tabular-nums ${
            isPositive ? "text-emerald-400" : "text-red-400"
          }`}
        >
          {isPositive ? "+" : ""}{position.pct_change.toFixed(1)}%
        </span>
      </div>
    </button>
  );
}

function OpportunitiesSection({
  onSelectOpportunity,
}: {
  onSelectOpportunity: (id: string) => void;
}) {
  const { data: opportunities, isLoading } = useOpportunities();
  const opps = opportunities ?? [];

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="shimmer h-[60px] rounded-lg" />
        ))}
      </div>
    );
  }

  if (opps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-2">
        <FileText className="h-6 w-6" />
        <p className={`${FontSize.medium} font-mono tracking-wider`}>NO OPPORTUNITIES</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {opps.map((opp) => (
        <MobileOpportunityRow
          key={opp.id}
          opportunity={opp}
          onSelect={() => onSelectOpportunity(opp.id)}
        />
      ))}
    </div>
  );
}

const statusColors: Record<string, { dot: string; text: string }> = {
  pending:     { dot: "bg-yellow-500",  text: Base.yellowStatus },
  researched:  { dot: "bg-sky-500",     text: Base.skyStatus },
  recommended: { dot: "bg-emerald-500", text: Base.emeraldStatus },
  traded:      { dot: "bg-violet-500",  text: Base.violetStatus },
  rejected:    { dot: "bg-red-500",     text: Muted.redLabel },
  expired:     { dot: "bg-zinc-600",    text: Muted.mutedText },
};

function MobileOpportunityRow({
  opportunity,
  onSelect,
}: {
  opportunity: OpportunitySummary;
  onSelect: () => void;
}) {
  const yesPercent = Math.round(opportunity.yes_price * 100);
  const status = statusColors[opportunity.status] ?? statusColors.pending;

  let relativeTime = "";
  try {
    const d = new Date(opportunity.discovered_at);
    if (isValid(d)) {
      relativeTime = formatDistanceToNow(d, { addSuffix: false });
    }
  } catch {
    /* skip */
  }

  return (
    <button
      onClick={onSelect}
      className="w-full text-left px-3 py-2.5 rounded-lg border border-transparent hover:bg-secondary/40 hover:border-border/60 transition-colors"
    >
      <div className="flex items-start gap-2">
        <span className={`mt-1.5 shrink-0 h-1.5 w-1.5 rounded-full ${status.dot}`} />
        <div className="flex-1 min-w-0">
          <p className={`${FontSize.medium} font-medium leading-snug line-clamp-2 ${Soft.foreground}`}>
            {opportunity.title}
          </p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`${FontSize.small} font-mono uppercase tracking-wider ${status.text}`}>
              {opportunity.status}
            </span>
            <div className="flex items-center gap-1.5">
              <div className="prob-bar-track w-10">
                <div className="prob-bar-yes" style={{ width: `${yesPercent}%` }} />
              </div>
              <span className={`${FontSize.small} font-mono ${Muted.mutedText} tabular-nums`}>
                {yesPercent}c
              </span>
            </div>
            <span className="flex-1" />
            <span className={`${FontSize.small} font-mono ${Muted.mutedText} tabular-nums shrink-0`}>
              {relativeTime}
            </span>
          </div>
        </div>
        <ChevronRight className={`h-3.5 w-3.5 shrink-0 mt-1 ${Muted.mutedText}`} />
      </div>
    </button>
  );
}

function LedgerSection({
  onSelectOpportunity,
}: {
  onSelectOpportunity: (id: string) => void;
}) {
  const { data: entries, isLoading } = useLedger(150);
  const allEntries = entries ?? [];
  const closes = allEntries.filter((e) => e.type === "close" && e.pnl != null);
  const wins = closes.filter((e) => (e.pnl ?? 0) > 0).length;
  const winRate = closes.length > 0 ? Math.round((wins / closes.length) * 100) : null;

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="shimmer h-10 rounded" />
        ))}
      </div>
    );
  }

  if (allEntries.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground gap-2">
        <Receipt className="h-6 w-6" />
        <p className={`${FontSize.medium} font-mono tracking-wider`}>NO TRADES</p>
      </div>
    );
  }

  const grouped = groupByDate(allEntries);

  return (
    <div className="flex flex-col gap-2.5">
      {/* Ledger header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs font-semibold text-foreground/70 tracking-[0.15em]">
            LEDGER
          </span>
          {winRate !== null && (
            <span
              className={`font-mono text-[11px] font-medium tabular-nums ${
                winRate >= 60
                  ? "text-emerald-400"
                  : winRate >= 40
                    ? "text-amber-400/70"
                    : "text-red-400"
              }`}
            >
              {winRate}% win
            </span>
          )}
        </div>
        <span className="font-mono text-[11px] font-medium text-muted-foreground tabular-nums">
          {allEntries.length}
        </span>
      </div>

      {/* Grouped entries */}
      {grouped.map(([dateLabel, dayEntries]) => (
        <div key={dateLabel} className="flex flex-col gap-1.5">
          <span className="font-mono text-[10px] font-medium text-muted-foreground/50 uppercase tracking-[0.1em]">
            {dateLabel}
          </span>
          {dayEntries.map((entry) => (
            <MobileLedgerRow
              key={entry.id}
              entry={entry}
              onSelect={() =>
                entry.opportunity_id && onSelectOpportunity(entry.opportunity_id)
              }
            />
          ))}
        </div>
      ))}
    </div>
  );
}

function MobileLedgerRow({
  entry,
  onSelect,
}: {
  entry: LedgerEntry;
  onSelect: () => void;
}) {
  const isBuy = entry.type === "buy";
  const pnl = entry.pnl ?? 0;

  const borderColor = isBuy
    ? "border-l-sky-400"
    : pnl > 0
      ? "border-l-emerald-400"
      : pnl < 0
        ? "border-l-red-400"
        : "border-l-border";

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left rounded-md bg-card border-l-[3px] ${borderColor} px-3 py-2 flex flex-col gap-0.5`}
    >
      <span className="font-mono text-[11px] font-medium text-foreground/80 truncate">
        {isBuy ? "BUY" : "SELL"} {entry.market_ticker} {"·"} x{entry.contracts}
      </span>
      <span className="font-mono text-[10px] text-muted-foreground">
        Filled {Math.round(entry.price * 100)}c
        {!isBuy && (
          <span className={pnl >= 0 ? " text-emerald-400" : " text-red-400"}>
            {" \u00B7 "}{pnl >= 0 ? "+" : ""}${pnl.toFixed(2)}
          </span>
        )}
      </span>
    </button>
  );
}

function groupByDate(entries: LedgerEntry[]): [string, LedgerEntry[]][] {
  const map = new Map<string, LedgerEntry[]>();
  for (const entry of entries) {
    let dateKey = "Unknown";
    try {
      const d = parseISO(entry.timestamp);
      if (isValid(d)) dateKey = format(d, "MMM d").toUpperCase();
    } catch {
      /* keep Unknown */
    }
    const existing = map.get(dateKey) ?? [];
    map.set(dateKey, [...existing, entry]);
  }
  return Array.from(map.entries());
}
