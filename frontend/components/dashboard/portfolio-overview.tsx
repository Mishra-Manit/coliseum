"use client";

import {
  DollarSign,
  Wallet,
  TrendingUp,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePortfolioState } from "@/hooks/use-api";

export function PortfolioOverview() {
  const { data: state, isLoading } = usePortfolioState();

  const totalValue = state?.portfolio?.total_value ?? 0;
  const cashBalance = state?.portfolio?.cash_balance ?? 0;
  const positionsValue = state?.portfolio?.positions_value ?? 0;
  const openCount = state?.open_positions?.length ?? 0;
  const closedCount = state?.closed_positions?.length ?? 0;
  const totalPnl =
    state?.closed_positions?.reduce((sum, p) => sum + p.pnl, 0) ?? 0;

  const cards = [
    {
      title: "Portfolio Value",
      value: `$${totalValue.toFixed(2)}`,
      icon: Wallet,
      description: "Total portfolio value",
      trend: null as string | null,
      accent: "from-amber-500/20 to-amber-600/5",
      iconColor: "text-amber-500",
    },
    {
      title: "Cash Balance",
      value: `$${cashBalance.toFixed(2)}`,
      icon: DollarSign,
      description: "Available to trade",
      trend: null as string | null,
      accent: "from-emerald-500/20 to-emerald-600/5",
      iconColor: "text-emerald-500",
    },
    {
      title: "Positions",
      value: `$${positionsValue.toFixed(2)}`,
      icon: BarChart3,
      description: `${openCount} open / ${closedCount} closed`,
      trend: null as string | null,
      accent: "from-sky-500/20 to-sky-600/5",
      iconColor: "text-sky-500",
    },
    {
      title: "Realized P&L",
      value: `${totalPnl >= 0 ? "+" : ""}$${totalPnl.toFixed(2)}`,
      icon: TrendingUp,
      description: "From closed positions",
      trend: totalPnl >= 0 ? "up" : "down",
      accent:
        totalPnl >= 0
          ? "from-emerald-500/20 to-emerald-600/5"
          : "from-red-500/20 to-red-600/5",
      iconColor: totalPnl >= 0 ? "text-emerald-500" : "text-red-500",
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
                {card.trend === "up" && (
                  <ArrowUpRight className="h-4 w-4 text-emerald-500" />
                )}
                {card.trend === "down" && (
                  <ArrowDownRight className="h-4 w-4 text-red-500" />
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1.5">
                {card.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
