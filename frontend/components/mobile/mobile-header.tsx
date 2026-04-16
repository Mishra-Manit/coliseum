"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useConfig, useDaemonStatus } from "@/hooks/use-api";

interface MobileHeaderProps {
  showChartLink?: boolean;
}

export function MobileHeader({ showChartLink = false }: MobileHeaderProps) {
  const { data: config } = useConfig();
  const { data: daemon } = useDaemonStatus();
  const pathname = usePathname();

  const paperMode =
    (config?.trading as Record<string, unknown>)?.paper_mode ?? true;
  const isOnline = daemon?.available ?? false;
  const isPaused = daemon?.paused ?? false;

  return (
    <div className="shrink-0 flex items-center justify-between h-11 px-5 bg-card border-b border-border">
      {/* Left: wordmark + badge */}
      <div className="flex items-center gap-2.5">
        <span className="font-mono text-xs font-bold text-foreground tracking-[0.2em] uppercase">
          Coliseum
        </span>
        {paperMode ? (
          <Badge
            variant="outline"
            className="border-yellow-600/25 bg-yellow-600/8 text-yellow-500/70 text-[11px] h-[18px] px-1.5 font-mono tracking-wider"
          >
            PAPER
          </Badge>
        ) : (
          <Badge
            variant="outline"
            className="border-emerald-600/25 bg-emerald-600/8 text-emerald-400/70 text-[11px] h-[18px] px-1.5 font-mono tracking-wider"
          >
            LIVE
          </Badge>
        )}
      </div>

      {/* Right: chart link + status dot */}
      <div className="flex items-center gap-3">
        {showChartLink && (
          <Link
            href={pathname === "/chart" ? "/" : "/chart"}
            className={`flex items-center gap-1 ${
              pathname === "/chart"
                ? "text-primary"
                : "text-muted-foreground/60"
            }`}
          >
            <BarChart3 className="h-3 w-3" />
            <span className="font-mono text-[11px] font-medium tracking-[0.13em] uppercase">
              Charts
            </span>
          </Link>
        )}
        <div
          className={`h-2 w-2 rounded-full ${
            !isOnline
              ? "bg-zinc-600"
              : isPaused
                ? "bg-yellow-500"
                : "bg-emerald-500"
          }`}
        />
      </div>
    </div>
  );
}
