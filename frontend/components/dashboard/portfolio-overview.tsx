"use client";

import {
  DollarSign,
  Wallet,
  BarChart3,
  Activity,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePortfolioState, useDaemonStatus } from "@/hooks/use-api";

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

export function PortfolioOverview() {
  const { data: state, isLoading } = usePortfolioState();
  const { data: daemon } = useDaemonStatus();

  const totalValue = state?.portfolio?.total_value ?? 0;
  const cashBalance = state?.portfolio?.cash_balance ?? 0;
  const positionsValue = state?.portfolio?.positions_value ?? 0;
  const openCount = state?.open_positions?.length ?? 0;
  const closedCount = state?.closed_positions?.length ?? 0;

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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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

      {/* Daemon status card */}
      <Card className="bg-card border-border overflow-hidden relative">
        <div
          className={`absolute inset-0 bg-gradient-to-br transition-opacity duration-300 ${
            !daemon?.available
              ? "from-zinc-500/10 to-zinc-600/5 opacity-100"
              : daemon.paused
                ? "from-yellow-500/15 to-yellow-600/5 opacity-100"
                : "from-emerald-500/15 to-emerald-600/5 opacity-100"
          }`}
        />
        <CardContent className="p-5 relative">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Daemon
            </span>
            <div
              className={`p-1.5 rounded-lg bg-secondary/80 ${
                !daemon?.available
                  ? "text-zinc-500"
                  : daemon.paused
                    ? "text-yellow-500"
                    : "text-emerald-500"
              }`}
            >
              <Activity className="h-3.5 w-3.5" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-foreground font-mono tracking-tight">
              {!daemon?.available
                ? "Offline"
                : daemon.paused
                  ? "Paused"
                  : "Running"}
            </span>
            {daemon?.available && !daemon.paused && (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1.5">
            {!daemon?.available
              ? "Start with: coliseum daemon"
              : daemon.paused
                ? `Paused — ${daemon.consecutive_failures} failures`
                : `${daemon.cycles_completed} cycles · up ${formatUptime(daemon.uptime_seconds)}`}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
