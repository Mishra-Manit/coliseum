"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useConfig, useDaemonStatus, usePortfolioState } from "@/hooks/use-api";
import { SettingsModal } from "@/components/dashboard/settings-modal";
import { FontSize } from "@/lib/typography";
import { Muted, Base, Faint, BgTint, BorderTint } from "@/lib/styles";

export function DashboardNavbar() {
  const { data: config } = useConfig();
  const { data: daemon } = useDaemonStatus();
  const { data: portfolio } = usePortfolioState();
  const pathname = usePathname();

  const paperMode =
    (config?.trading as Record<string, unknown>)?.paper_mode ?? true;

  const isOnline = daemon?.available ?? false;
  const isPaused = daemon?.paused ?? false;

  const totalValue = portfolio?.portfolio?.total_value ?? 0;
  const cashBalance = portfolio?.portfolio?.cash_balance ?? 0;
  const openCount = portfolio?.open_positions?.length ?? 0;

  return (
    <nav className={`sticky top-0 z-50 h-11 border-b border-border ${Base.card} backdrop-blur-xl flex items-center px-5`}>
      {/* Wordmark */}
      <div className="flex items-center gap-3 shrink-0">
        <span className="font-mono text-xs font-bold text-foreground tracking-[0.2em] uppercase">
          Coliseum
        </span>
        {paperMode ? (
          <Badge
            variant="outline"
            className={`${BorderTint.paperBadge} ${BgTint.paperBadge} ${Muted.yellowBadge} ${FontSize.small} h-[18px] px-1.5 font-mono tracking-wider`}
          >
            PAPER
          </Badge>
        ) : (
          <Badge
            variant="outline"
            className={`${BorderTint.liveBadge} ${BgTint.liveBadge} ${Muted.emeraldLabel} ${FontSize.small} h-[18px] px-1.5 font-mono tracking-wider`}
          >
            LIVE
          </Badge>
        )}
      </div>

      <div className="w-px h-4 bg-border mx-5 shrink-0" />

      {/* Core stats: NAV, CASH, POS */}
      <div className="flex items-center gap-6 flex-1 min-w-0 overflow-hidden">
        <StatPill label="NAV" value={`$${totalValue.toFixed(2)}`} />
        <StatPill label="CASH" value={`$${cashBalance.toFixed(2)}`} />
        <StatPill
          label="POS"
          value={String(openCount)}
          dimmed={openCount === 0}
        />
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-3 shrink-0">
        <Link
          href={pathname === "/chart" ? "/" : "/chart"}
          className={`flex items-center gap-1.5 px-2 py-0.5 rounded transition-colors ${
            pathname === "/chart"
              ? "text-primary bg-primary/10"
              : `${Faint.mutedText} hover:text-muted-foreground`
          }`}
        >
          <BarChart2 className="w-3 h-3" />
          <span className={`${FontSize.small} font-mono tracking-[0.12em] uppercase`}>
            Charts
          </span>
        </Link>

        <div className="w-px h-4 bg-border shrink-0" />

        <SettingsModal />

        <div className="flex items-center gap-2 pl-3 border-l border-border">
          <span className="relative flex h-1.5 w-1.5">
            {isOnline && !isPaused && (
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 ${Faint.opacityClass}`} />
            )}
            <span
              className={`relative inline-flex rounded-full h-1.5 w-1.5 ${
                !isOnline
                  ? "bg-zinc-600"
                  : isPaused
                    ? "bg-yellow-500"
                    : "bg-emerald-500"
              }`}
            />
          </span>
          <span className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-wider`}>
            {!isOnline ? "OFFLINE" : isPaused ? "PAUSED" : "RUNNING"}
          </span>
        </div>
      </div>
    </nav>
  );
}

function StatPill({
  label,
  value,
  dimmed = false,
}: {
  label: string;
  value: string;
  dimmed?: boolean;
}) {
  return (
    <div className="flex items-baseline gap-1.5 shrink-0">
      <span className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-[0.12em] uppercase`}>
        {label}
      </span>
      <span
        className={`${FontSize.medium} font-mono font-medium tabular-nums ${
          dimmed ? Muted.mutedText : Base.foreground
        }`}
      >
        {value}
      </span>
    </div>
  );
}
