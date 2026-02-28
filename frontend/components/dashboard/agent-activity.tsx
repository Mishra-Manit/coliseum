"use client";

import { formatDistanceToNow } from "date-fns";
import {
  Search,
  Microscope,
  Calculator,
  ShoppingCart,
  Shield,
  Circle,
  Clock,
  CheckCircle2,
  ChevronDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useAgentStatus, useAgentActivity } from "@/hooks/use-api";

const agentIcons: Record<string, typeof Search> = {
  scout: Search,
  analyst_researcher: Microscope,
  analyst_recommender: Calculator,
  trader: ShoppingCart,
  guardian: Shield,
};

const agentAccents: Record<string, { bg: string; text: string; dot: string }> = {
  scout: {
    bg: "bg-sky-500/10",
    text: "text-sky-400",
    dot: "bg-sky-400",
  },
  analyst_researcher: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    dot: "bg-amber-400",
  },
  analyst_recommender: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    dot: "bg-emerald-400",
  },
  trader: {
    bg: "bg-violet-500/10",
    text: "text-violet-400",
    dot: "bg-violet-400",
  },
  guardian: {
    bg: "bg-rose-500/10",
    text: "text-rose-400",
    dot: "bg-rose-400",
  },
};

const statusStyles: Record<string, string> = {
  idle: "bg-secondary text-muted-foreground",
  running: "bg-amber-500/15 text-amber-400 animate-pulse",
  error: "bg-red-500/15 text-red-400",
};

export function AgentActivity() {
  const { data: agentStatus, isLoading: statusLoading } = useAgentStatus();
  const { data: activity, isLoading: activityLoading } = useAgentActivity();

  if (statusLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <Skeleton className="h-5 w-32 bg-secondary" />
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-9 w-9 rounded-lg bg-secondary" />
              <div className="flex-1">
                <Skeleton className="h-4 w-24 bg-secondary mb-1" />
                <Skeleton className="h-3 w-40 bg-secondary" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  const agents = agentStatus?.agents ?? [];

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="font-display text-lg font-semibold text-foreground">
            Agent Pipeline
          </CardTitle>
          <div className="flex items-center gap-2">
            {agentStatus?.paper_mode && (
              <Badge
                variant="outline"
                className="border-yellow-600/40 bg-yellow-600/10 text-yellow-500 text-[10px] font-mono"
              >
                PAPER
              </Badge>
            )}
            <Badge
              variant="outline"
              className="border-border bg-secondary/50 text-muted-foreground text-[10px] font-mono uppercase"
            >
              {agentStatus?.strategy ?? "edge"}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-0.5 pt-0">
        {agents.map((agent, index) => {
          const Icon = agentIcons[agent.name] ?? Circle;
          const accent = agentAccents[agent.name] ?? {
            bg: "bg-secondary",
            text: "text-muted-foreground",
            dot: "bg-muted-foreground",
          };

          return (
            <div key={agent.name}>
              <div className="flex items-center gap-3 py-2.5 px-3 rounded-xl hover:bg-secondary/50 transition-colors group">
                <div className={`p-2 rounded-lg ${accent.bg}`}>
                  <Icon className={`h-4 w-4 ${accent.text}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-foreground">
                      {agent.display_name}
                    </span>
                    <Badge
                      className={`text-[9px] px-1.5 py-0 h-4 rounded-md font-mono ${
                        statusStyles[agent.status] ?? statusStyles.idle
                      }`}
                    >
                      {agent.status}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground truncate mt-0.5">
                    {agent.description}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  {agent.last_run ? (
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                      <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                      <span>
                        {formatDistanceToNow(new Date(agent.last_run), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                  ) : (
                    <span className="text-[10px] text-muted-foreground/40">
                      No runs yet
                    </span>
                  )}
                  {agent.schedule_interval_minutes && (
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground/60 mt-0.5 justify-end">
                      <Clock className="h-2.5 w-2.5" />
                      Every {agent.schedule_interval_minutes}m
                    </div>
                  )}
                </div>
              </div>
              {index < agents.length - 1 && (
                <div className="ml-7 flex items-center gap-0 py-0.5">
                  <ChevronDown className="h-3 w-3 text-border" />
                </div>
              )}
            </div>
          );
        })}
      </CardContent>

      {activity && activity.length > 0 && (
        <>
          <Separator className="bg-border" />
          <CardContent className="pt-4">
            <p className="text-[10px] font-semibold text-muted-foreground mb-3 uppercase tracking-widest">
              Recent Activity
            </p>
            <ScrollArea className="h-[160px]">
              <div className="space-y-2.5">
                {activity.slice(0, 10).map((item, i) => {
                  const Icon = agentIcons[item.agent] ?? Circle;
                  const accent = agentAccents[item.agent] ?? {
                    bg: "bg-secondary",
                    text: "text-muted-foreground",
                    dot: "bg-muted-foreground",
                  };
                  const actionLabel = item.action
                    .replace(/_/g, " ")
                    .replace(/\b\w/g, (c) => c.toUpperCase());

                  return (
                    <div
                      key={`${item.timestamp}-${i}`}
                      className="flex items-start gap-2.5 text-xs"
                    >
                      <div className={`mt-0.5 w-1.5 h-1.5 rounded-full shrink-0 ${accent.dot}`} />
                      <div className="min-w-0 flex-1">
                        <span className="text-foreground font-medium">
                          {actionLabel}
                        </span>
                        <span className="text-muted-foreground ml-1.5 font-mono text-[11px] truncate block">
                          {item.market_ticker}
                        </span>
                      </div>
                      <span className="text-muted-foreground/50 shrink-0 text-[10px]">
                        {formatDistanceToNow(new Date(item.timestamp), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          </CardContent>
        </>
      )}
    </Card>
  );
}
