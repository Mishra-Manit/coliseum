"use client";

import { formatDistanceToNow } from "date-fns";
import { FileText, ChevronRight } from "lucide-react";
import { useOpportunities } from "@/hooks/use-api";
import type { OpportunitySummary } from "@/lib/types";
import { FontSize } from "@/lib/typography";
import { Muted, Soft, Base, Strong, BgTint, BorderTint } from "@/lib/styles";

const statusColors: Record<string, { dot: string; text: string }> = {
  pending:    { dot: "bg-yellow-500",  text: Base.yellowStatus },
  researched: { dot: "bg-sky-500",     text: Base.skyStatus },
  recommended:{ dot: "bg-emerald-500", text: Base.emeraldStatus },
  traded:     { dot: "bg-violet-500",  text: Base.violetStatus },
  rejected:   { dot: "bg-red-500",     text: Muted.redLabel },
  expired:    { dot: "bg-zinc-600",    text: Muted.mutedText },
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
        <span className={`${FontSize.medium} font-mono ${Muted.mutedText} tracking-[0.15em] uppercase`}>
          Opportunities
        </span>
        <span className={`${FontSize.small} font-mono ${Muted.mutedText} tabular-nums`}>
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
          <div className={`flex flex-col items-center justify-center h-full min-h-[300px] ${Muted.mutedText} gap-2`}>
            <FileText className="h-6 w-6" />
            <p className={`${FontSize.medium} font-mono tracking-wider`}>NO OPPORTUNITIES</p>
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
          ? `${BgTint.amberBadge} border ${BorderTint.amberSelected}`
          : "border border-transparent hover:bg-secondary/40 hover:border-border/60"
      }`}
    >
      <div className="flex items-start gap-2">
        {/* Status dot */}
        <span
          className={`mt-1.5 shrink-0 h-1.5 w-1.5 rounded-full ${status.dot}`}
        />

        <div className="flex-1 min-w-0">
          {/* Event context */}
          {opportunity.event_title && (
            <p className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-wide truncate mb-0.5`}>
              {opportunity.event_title}
            </p>
          )}

          {/* Title */}
          <p
            className={`${FontSize.medium} font-medium leading-snug line-clamp-2 transition-colors ${
              isSelected ? "text-foreground" : `${Soft.foreground} ${Strong.foregroundGroupHover}`
            }`}
          >
            {opportunity.title}
          </p>

          {/* Bottom row */}
          <div className="flex items-center gap-3 mt-1.5">
            {/* Status label */}
            <span className={`${FontSize.small} font-mono uppercase tracking-wider ${status.text}`}>
              {opportunity.status}
            </span>

            {/* Action badge */}
            {opportunity.action && (
              <span
                className={`${FontSize.small} font-mono font-bold uppercase ${
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
              <span className={`${FontSize.small} font-mono ${Muted.mutedText} tabular-nums w-6 text-right`}>
                {yesPercent}c
              </span>
            </div>
          </div>
        </div>

        <ChevronRight
          className={`h-3.5 w-3.5 shrink-0 mt-1 transition-all duration-150 ${
            isSelected
              ? Muted.amberLabel
              : `${Muted.mutedText} ${Muted.mutedTextGroupHover}`
          }`}
        />
      </div>

      {/* Time */}
      <p className={`${FontSize.small} font-mono ${Muted.mutedText} mt-1.5 ml-3.5 tracking-wide`}>
        {formatDistanceToNow(new Date(opportunity.discovered_at), {
          addSuffix: true,
        })}
      </p>
    </button>
  );
}
