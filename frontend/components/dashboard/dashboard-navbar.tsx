"use client";

import { RefreshCw, Settings } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useConfig } from "@/hooks/use-api";

export function DashboardNavbar() {
  const { data: config, mutate } = useConfig();

  const paperMode = (config?.trading as Record<string, unknown>)?.paper_mode ?? true;
  const strategy = config?.strategy ?? "...";

  return (
    <nav className="sticky top-0 z-50 h-16 bg-card/80 backdrop-blur-xl border-b border-border flex items-center justify-between px-8">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="font-display text-lg font-bold text-foreground tracking-tight leading-tight">
              Coliseum
            </h1>
            <p className="text-[11px] text-muted-foreground leading-tight tracking-wide uppercase">
              Trading Dashboard
            </p>
          </div>
        </div>

        <div className="h-8 w-px bg-border mx-1" />

        <div className="flex items-center gap-2">
          {paperMode ? (
            <Badge
              variant="outline"
              className="border-yellow-600/40 bg-yellow-600/10 text-yellow-500 text-[10px] h-5 font-mono tracking-wider"
            >
              PAPER
            </Badge>
          ) : (
            <Badge
              variant="outline"
              className="border-emerald-600/40 bg-emerald-600/10 text-emerald-400 text-[10px] h-5 font-mono tracking-wider"
            >
              LIVE
            </Badge>
          )}
          <Badge
            variant="outline"
            className="border-border bg-secondary/50 text-muted-foreground text-[10px] h-5 font-mono uppercase tracking-wider"
          >
            {strategy}
          </Badge>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => mutate()}
          className="p-2.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          title="Refresh data"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
        <button
          className="p-2.5 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          title="Settings"
        >
          <Settings className="h-4 w-4" />
        </button>
        <div className="flex items-center gap-2 ml-3 pl-3 border-l border-border">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs text-muted-foreground font-medium">
            Connected
          </span>
        </div>
      </div>
    </nav>
  );
}
