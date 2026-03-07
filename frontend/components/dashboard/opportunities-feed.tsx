"use client";

import { formatDistanceToNow } from "date-fns";
import { FileText, ChevronRight } from "lucide-react";
import { useOpportunities } from "@/hooks/use-api";
import type { OpportunitySummary } from "@/lib/types";

const statusColors: Record<string, { dot: string; text: string }> = {
  pending:    { dot: "bg-yellow-500",  text: "text-yellow-500/80" },
  researched: { dot: "bg-sky-500",     text: "text-sky-400/80" },
  recommended:{ dot: "bg-emerald-500", text: "text-emerald-400/80" },
  traded:     { dot: "bg-violet-500",  text: "text-violet-400/80" },
  rejected:   { dot: "bg-red-500",     text: "text-red-400/60" },
  expired:    { dot: "bg-zinc-600",    text: "text-muted-foreground/40" },
};

interface OpportunitiesFeedProps {
  onSelectOpportunity?: (id: string) => void;
  selectedId?: string | null;
}

export function OpportunitiesFeed({
  onSelectOpportunity,
  selectedId,
}: OpportunitiesFeedProps) {
  const { data: opportunities, isLoading } = useOpportunities();
  const opps = opportunities ?? [];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <span className="text-[11px] font-mono text-muted-foreground/50 tracking-[0.15em] uppercase">
          Opportunities
        </span>
        <span className="text-[10px] font-mono text-muted-foreground/30 tabular-nums">
          {opps.length}
        </span>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto min-h-0">
        {isLoading ? (
          <div className="p-3 space-y-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="shimmer h-[72px] rounded" />
            ))}
          </div>
        ) : opps.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[300px] text-muted-foreground/30 gap-2">
            <FileText className="h-6 w-6" />
            <p className="text-[11px] font-mono tracking-wider">NO OPPORTUNITIES</p>
          </div>
        ) : (
          <div className="p-2 space-y-0.5">
            {opps.map((opp) => (
              <OpportunityRow
                key={opp.id}
                opportunity={opp}
                isSelected={selectedId === opp.id}
                onSelect={() => onSelectOpportunity?.(opp.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function OpportunityRow({
  opportunity,
  isSelected,
  onSelect,
}: {
  opportunity: OpportunitySummary;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const yesPercent = Math.round(opportunity.yes_price * 100);
  const status = statusColors[opportunity.status] ?? statusColors.pending;

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left px-3 py-2.5 rounded transition-all duration-150 group ${
        isSelected
          ? "bg-amber-500/6 border border-amber-600/20"
          : "border border-transparent hover:bg-secondary/40 hover:border-border/60"
      }`}
    >
      <div className="flex items-start gap-2">
        {/* Status dot */}
        <span
          className={`mt-1.5 shrink-0 h-1.5 w-1.5 rounded-full ${status.dot}`}
        />

        <div className="flex-1 min-w-0">
          {/* Title */}
          <p
            className={`text-[12px] font-medium leading-snug line-clamp-2 transition-colors ${
              isSelected ? "text-foreground" : "text-foreground/75 group-hover:text-foreground/90"
            }`}
          >
            {opportunity.title}
          </p>

          {/* Bottom row */}
          <div className="flex items-center gap-3 mt-1.5">
            {/* Status label */}
            <span className={`text-[9px] font-mono uppercase tracking-wider ${status.text}`}>
              {opportunity.status}
            </span>

            {/* Action badge */}
            {opportunity.action && (
              <span
                className={`text-[9px] font-mono font-bold uppercase ${
                  opportunity.action.includes("YES")
                    ? "text-emerald-400"
                    : opportunity.action.includes("NO")
                      ? "text-red-400"
                      : "text-muted-foreground"
                }`}
              >
                {opportunity.action}
              </span>
            )}

            {/* Spacer */}
            <span className="flex-1" />

            {/* Yes probability bar */}
            <div className="flex items-center gap-1.5">
              <div className="prob-bar-track w-14">
                <div
                  className="prob-bar-yes"
                  style={{ width: `${yesPercent}%` }}
                />
              </div>
              <span className="text-[9px] font-mono text-muted-foreground/40 tabular-nums w-6 text-right">
                {yesPercent}c
              </span>
            </div>
          </div>
        </div>

        <ChevronRight
          className={`h-3.5 w-3.5 shrink-0 mt-1 transition-all duration-150 ${
            isSelected
              ? "text-amber-500/70"
              : "text-muted-foreground/20 group-hover:text-muted-foreground/40"
          }`}
        />
      </div>

      {/* Time */}
      <p className="text-[9px] font-mono text-muted-foreground/25 mt-1.5 ml-3.5 tracking-wide">
        {formatDistanceToNow(new Date(opportunity.discovered_at), {
          addSuffix: true,
        })}
      </p>
    </button>
  );
}
