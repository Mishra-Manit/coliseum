"use client";

import { useState } from "react";
import {
  DollarSign,
  Wallet,
  BarChart3,
  Play,
  Loader2,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePortfolioState, usePipelineStatus } from "@/hooks/use-api";
import { post } from "@/lib/api";

export function PortfolioOverview() {
  const { data: state, isLoading } = usePortfolioState();
  const { data: pipelineStatus, mutate: mutatePipeline } = usePipelineStatus();

  const [triggerError, setTriggerError] = useState<string | null>(null);

  const totalValue = state?.portfolio?.total_value ?? 0;
  const cashBalance = state?.portfolio?.cash_balance ?? 0;
  const positionsValue = state?.portfolio?.positions_value ?? 0;
  const openCount = state?.open_positions?.length ?? 0;
  const closedCount = state?.closed_positions?.length ?? 0;

  const pipelineRunning = pipelineStatus?.running ?? false;

  const handleRunPipeline = async () => {
    setTriggerError(null);
    try {
      await post("/api/pipeline/run");
      await mutatePipeline();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to trigger pipeline";
      if (message.includes("409")) {
        setTriggerError("Already running");
      } else {
        setTriggerError("Failed to start");
      }
    }
  };

  const cards = [
    {
      title: "Portfolio Value",
      value: `$${totalValue.toFixed(2)}`,
      icon: Wallet,
      description: "Total portfolio value",
      accent: "from-amber-500/20 to-amber-600/5",
      iconColor: "text-amber-500",
    },
    {
      title: "Cash Balance",
      value: `$${cashBalance.toFixed(2)}`,
      icon: DollarSign,
      description: "Available to trade",
      accent: "from-emerald-500/20 to-emerald-600/5",
      iconColor: "text-emerald-500",
    },
    {
      title: "Positions",
      value: `$${positionsValue.toFixed(2)}`,
      icon: BarChart3,
      description: `${openCount} open / ${closedCount} closed`,
      accent: "from-sky-500/20 to-sky-600/5",
      iconColor: "text-sky-500",
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="bg-card border-border">
            <CardContent className="p-5">
              <Skeleton className="h-4 w-24 bg-secondary mb-3" />
              <Skeleton className="h-8 w-20 bg-secondary mb-2" />
              <Skeleton className="h-3 w-32 bg-secondary" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card
            key={card.title}
            className="bg-card border-border hover:border-amber-700/30 transition-all duration-200 group overflow-hidden relative"
          >
            <div
              className={`absolute inset-0 bg-gradient-to-br ${card.accent} opacity-0 group-hover:opacity-100 transition-opacity duration-300`}
            />
            <CardContent className="p-5 relative">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                  {card.title}
                </span>
                <div className={`p-1.5 rounded-lg bg-secondary/80 ${card.iconColor}`}>
                  <Icon className="h-3.5 w-3.5" />
                </div>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold text-foreground font-mono tracking-tight">
                  {card.value}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1.5">
                {card.description}
              </p>
            </CardContent>
          </Card>
        );
      })}

      {/* Pipeline trigger card */}
      <Card
        className={`border-border transition-all duration-200 group overflow-hidden relative ${
          pipelineRunning
            ? "bg-card border-amber-700/40"
            : "bg-card hover:border-amber-700/30 cursor-pointer"
        }`}
        onClick={pipelineRunning ? undefined : handleRunPipeline}
      >
        <div
          className={`absolute inset-0 bg-gradient-to-br ${
            pipelineRunning
              ? "from-amber-500/15 to-amber-600/5 opacity-100"
              : "from-violet-500/20 to-violet-600/5 opacity-0 group-hover:opacity-100"
          } transition-opacity duration-300`}
        />
        <CardContent className="p-5 relative">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              {pipelineRunning ? "Pipeline Running" : "Run Pipeline"}
            </span>
            <div
              className={`p-1.5 rounded-lg bg-secondary/80 ${
                pipelineRunning ? "text-amber-500" : "text-violet-500"
              }`}
            >
              {pipelineRunning ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="h-3.5 w-3.5" />
              )}
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-foreground font-mono tracking-tight">
              {pipelineRunning ? "Active" : "Ready"}
            </span>
            {pipelineRunning && (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-500 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500" />
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1.5">
            {triggerError
              ? triggerError
              : pipelineRunning
                ? "Guardian > Scout > Analyst > Trader"
                : "Full cycle: scan, analyze, trade"}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
