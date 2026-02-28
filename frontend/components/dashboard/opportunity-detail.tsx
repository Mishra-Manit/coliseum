"use client";

import { formatDistanceToNow, format } from "date-fns";
import {
  X,
  Clock,
  Target,
  TrendingUp,
  TrendingDown,
  FileText,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useOpportunityDetail } from "@/hooks/use-api";

interface OpportunityDetailProps {
  opportunityId: string | null;
  onClose: () => void;
}

export function OpportunityDetailView({
  opportunityId,
  onClose,
}: OpportunityDetailProps) {
  const { data, isLoading } = useOpportunityDetail(opportunityId);

  if (!opportunityId) {
    return (
      <Card className="bg-card border-border h-full flex items-center justify-center min-h-[500px]">
        <div className="text-center text-muted-foreground">
          <div className="w-16 h-16 rounded-2xl bg-secondary/50 flex items-center justify-center mx-auto mb-4">
            <FileText className="h-7 w-7 opacity-30" />
          </div>
          <p className="text-sm font-semibold">Select an opportunity</p>
          <p className="text-xs mt-1.5 opacity-60 max-w-[200px] mx-auto">
            Click on any opportunity to view its full analysis from the agents
          </p>
        </div>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader className="pb-4">
          <Skeleton className="h-6 w-3/4 bg-secondary" />
          <Skeleton className="h-4 w-1/2 bg-secondary mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Skeleton className="h-20 w-full bg-secondary rounded-xl" />
            <Skeleton className="h-20 w-full bg-secondary rounded-xl" />
          </div>
          <Skeleton className="h-px w-full bg-secondary" />
          <Skeleton className="h-40 w-full bg-secondary rounded-xl" />
          <Skeleton className="h-60 w-full bg-secondary rounded-xl" />
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="bg-card border-border h-full flex items-center justify-center min-h-[500px]">
        <div className="text-center text-muted-foreground">
          <p className="text-sm font-medium">Opportunity not found</p>
        </div>
      </Card>
    );
  }

  const { summary, markdown_body } = data;
  const yesPercent = Math.round(summary.yes_price * 100);
  const noPercent = Math.round(summary.no_price * 100);

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <CardTitle className="font-display text-xl font-bold text-foreground leading-tight">
              {summary.title}
            </CardTitle>
            {summary.subtitle && (
              <p className="text-sm text-muted-foreground mt-1.5">
                {summary.subtitle}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-secondary text-muted-foreground shrink-0 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap mt-3">
          <Badge
            variant="outline"
            className="text-[10px] px-2 h-5 border-amber-600/30 bg-amber-500/10 text-amber-400 font-mono"
          >
            {summary.status}
          </Badge>
          <Badge
            variant="outline"
            className="text-[10px] px-2 h-5 border-border bg-secondary/50 text-muted-foreground font-mono"
          >
            {summary.strategy}
          </Badge>
          {summary.action && (
            <Badge
              variant="outline"
              className={`text-[10px] px-2 h-5 font-mono font-semibold ${
                summary.action.includes("YES")
                  ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                  : "border-red-500/30 bg-red-500/10 text-red-400"
              }`}
            >
              {summary.action}
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingUp className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">
                Yes
              </span>
            </div>
            <span className="text-2xl font-bold text-foreground font-mono">
              {yesPercent}c
            </span>
          </div>
          <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/10">
            <div className="flex items-center gap-1.5 mb-2">
              <TrendingDown className="h-3.5 w-3.5 text-red-500" />
              <span className="text-[11px] font-semibold text-red-400 uppercase tracking-wider">
                No
              </span>
            </div>
            <span className="text-2xl font-bold text-foreground font-mono">
              {noPercent}c
            </span>
          </div>
        </div>

        <div className="flex items-center gap-5 mt-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            Closes{" "}
            {summary.close_time
              ? formatDistanceToNow(new Date(summary.close_time), {
                  addSuffix: true,
                })
              : "N/A"}
          </span>
          <span className="flex items-center gap-1.5 font-mono text-[11px]">
            <Target className="h-3.5 w-3.5" />
            {summary.market_ticker}
          </span>
        </div>
      </CardHeader>

      <Separator className="bg-border" />

      <CardContent className="pt-5">
        <ScrollArea className="h-[calc(100vh-420px)] min-h-[400px] pr-3">
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {markdown_body}
            </ReactMarkdown>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
