"use client";

import { formatDistanceToNow } from "date-fns";
import {
  FileText,
  ChevronRight,
  TrendingUp,
  TrendingDown,
  Clock,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useOpportunities } from "@/hooks/use-api";
import type { OpportunitySummary } from "@/lib/types";

const statusVariants: Record<string, string> = {
  pending: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
  researched: "bg-sky-500/10 text-sky-400 border-sky-500/20",
  recommended: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  traded: "bg-violet-500/10 text-violet-400 border-violet-500/20",
  rejected: "bg-red-500/10 text-red-400 border-red-500/20",
  expired: "bg-secondary text-muted-foreground border-border",
};

const strategyLabels: Record<string, string> = {
  edge: "Edge",
  sure_thing: "Sure Thing",
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

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <Skeleton className="h-5 w-40 bg-secondary" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="p-4 rounded-xl bg-secondary/50 border border-border"
            >
              <Skeleton className="h-4 w-3/4 bg-secondary mb-3" />
              <Skeleton className="h-3 w-1/2 bg-secondary mb-3" />
              <div className="flex gap-2">
                <Skeleton className="h-5 w-16 rounded-md bg-secondary" />
                <Skeleton className="h-5 w-16 rounded-md bg-secondary" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  const opps = opportunities ?? [];

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="font-display text-lg font-semibold text-foreground">
            Opportunities
          </CardTitle>
          <Badge
            variant="outline"
            className="border-border bg-secondary/50 text-muted-foreground text-[10px] font-mono"
          >
            {opps.length} total
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <ScrollArea className="h-[calc(100vh-340px)] min-h-[400px] pr-2">
          <div className="space-y-2">
            {opps.map((opp) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                isSelected={selectedId === opp.id}
                onSelect={() => onSelectOpportunity?.(opp.id)}
              />
            ))}
            {opps.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-10 w-10 mx-auto mb-3 opacity-20" />
                <p className="text-sm font-medium">
                  No opportunities discovered yet
                </p>
                <p className="text-xs mt-1 opacity-60">
                  Run the Scout agent to scan markets
                </p>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function OpportunityCard({
  opportunity,
  isSelected,
  onSelect,
}: {
  opportunity: OpportunitySummary;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const yesPercent = Math.round(opportunity.yes_price * 100);
  const noPercent = Math.round(opportunity.no_price * 100);

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left p-4 rounded-xl border transition-all duration-200 ${
        isSelected
          ? "bg-amber-500/5 border-amber-600/30 shadow-sm shadow-amber-500/5"
          : "bg-secondary/30 border-border hover:border-amber-700/20 hover:bg-secondary/60"
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-sm font-semibold text-foreground leading-snug line-clamp-2">
          {opportunity.title}
        </h3>
        <ChevronRight
          className={`h-4 w-4 shrink-0 mt-0.5 transition-all duration-200 ${
            isSelected
              ? "text-amber-500 translate-x-0.5"
              : "text-muted-foreground/40"
          }`}
        />
      </div>

      {opportunity.subtitle && (
        <p className="text-xs text-muted-foreground mb-2.5 truncate">
          {opportunity.subtitle}
        </p>
      )}

      <div className="flex items-center gap-1.5 flex-wrap mb-3">
        <Badge
          variant="outline"
          className={`text-[10px] px-1.5 py-0 h-[18px] border font-mono ${
            statusVariants[opportunity.status] ?? statusVariants.pending
          }`}
        >
          {opportunity.status}
        </Badge>
        <Badge
          variant="outline"
          className="text-[10px] px-1.5 py-0 h-[18px] border-border text-muted-foreground font-mono"
        >
          {strategyLabels[opportunity.strategy] ?? opportunity.strategy}
        </Badge>
        {opportunity.action && (
          <Badge
            variant="outline"
            className={`text-[10px] px-1.5 py-0 h-[18px] font-mono font-semibold ${
              opportunity.action.includes("YES")
                ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/5"
                : opportunity.action.includes("NO")
                ? "border-red-500/30 text-red-400 bg-red-500/5"
                : "border-border text-muted-foreground"
            }`}
          >
            {opportunity.action}
          </Badge>
        )}
      </div>

      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 font-mono">
            <TrendingUp className="h-3 w-3 text-emerald-500" />
            YES {yesPercent}c
          </span>
          <span className="flex items-center gap-1 font-mono">
            <TrendingDown className="h-3 w-3 text-red-500" />
            NO {noPercent}c
          </span>
        </div>
        <span className="flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatDistanceToNow(new Date(opportunity.discovered_at), {
            addSuffix: true,
          })}
        </span>
      </div>
    </button>
  );
}
