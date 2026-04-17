"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useConfig } from "@/hooks/use-api";
import type { ColiseumConfig } from "@/lib/types";
import { useTimezone, type Timezone } from "@/lib/timezone-context";
import { MobileBottomNav } from "./mobile-bottom-nav";
import { Skeleton } from "@/components/ui/skeleton";

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function formatSeconds(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s > 0 ? `${m}m ${s}s` : `${m}m`;
}

type SettingRow = { label: string; value: string };
type Section = { title: string; rows: SettingRow[] };

function buildSections(config: ColiseumConfig): Section[] {
  const daemon = config.daemon ?? {};
  const execution = config.execution ?? {};
  const guardian = config.guardian ?? {};

  return [
    {
      title: "DAEMON",
      rows: [
        {
          label: "Pipeline cycle",
          value:
            typeof daemon.heartbeat_interval_minutes === "number"
              ? formatMinutes(daemon.heartbeat_interval_minutes as number)
              : "\u2014",
        },
        {
          label: "Guardian check interval",
          value:
            typeof daemon.guardian_interval_minutes === "number"
              ? formatMinutes(daemon.guardian_interval_minutes as number)
              : "\u2014",
        },
        {
          label: "Max failures",
          value:
            typeof daemon.max_consecutive_failures === "number"
              ? String(daemon.max_consecutive_failures)
              : "\u2014",
        },
      ],
    },
    {
      title: "EXECUTION",
      rows: [
        {
          label: "Order check interval",
          value:
            typeof execution.order_check_interval_seconds === "number"
              ? formatSeconds(execution.order_check_interval_seconds as number)
              : "\u2014",
        },
        {
          label: "Max order age",
          value:
            typeof execution.max_order_age_minutes === "number"
              ? formatMinutes(execution.max_order_age_minutes as number)
              : "\u2014",
        },
        {
          label: "Max reprice attempts",
          value:
            typeof execution.max_reprice_attempts === "number"
              ? String(execution.max_reprice_attempts)
              : "\u2014",
        },
      ],
    },
    {
      title: "GUARDIAN",
      rows: [
        {
          label: "Stop-loss threshold",
          value:
            typeof guardian.stop_loss_price === "number"
              ? `${Math.round((guardian.stop_loss_price as number) * 100)}\u00A2`
              : "\u2014",
        },
      ],
    },
  ];
}

export function MobileSettings() {
  const { data: config, isLoading } = useConfig();
  const { tz, setTz } = useTimezone();
  const paperMode =
    (config?.trading as Record<string, unknown>)?.paper_mode ?? true;

  const sections = config && !isLoading ? buildSections(config) : [];

  return (
    <div className="flex flex-col h-[100dvh] bg-background overflow-hidden">
      {/* Settings Header */}
      <div className="shrink-0 sticky top-0 z-50 flex items-center gap-3 h-[52px] pt-[env(safe-area-inset-top)] px-5 bg-card/95 backdrop-blur-sm border-b border-border">
        <Link href="/" className="text-foreground/80">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <span className="font-mono text-[13px] font-bold text-foreground/80 tracking-[0.18em]">
          SETTINGS
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0 px-5 py-6 flex flex-col gap-6">
        {/* Timezone */}
        <div className="flex flex-col gap-2.5">
          <span className="font-mono text-[10px] font-bold text-muted-foreground/50 tracking-[0.2em]">
            TIMEZONE
          </span>
          <div className="flex items-center border border-border rounded-md overflow-hidden self-start">
            {(["EST", "PST"] as Timezone[]).map((option) => (
              <button
                key={option}
                onClick={() => setTz(option)}
                className={`px-5 py-2 font-mono text-xs font-medium tracking-[0.12em] transition-colors border-r border-border last:border-r-0 ${
                  tz === option
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground/85"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        {/* Config sections */}
        {isLoading ? (
          <div className="flex flex-col gap-5">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex flex-col gap-2">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-32 w-full rounded-lg" />
              </div>
            ))}
          </div>
        ) : (
          sections.map((section) => (
            <div key={section.title} className="flex flex-col gap-2">
              <span className="font-mono text-[10px] font-bold text-muted-foreground/50 tracking-[0.2em]">
                {section.title}
              </span>
              <div className="rounded-lg bg-white/[0.03] border border-white/[0.08] overflow-hidden">
                {section.rows.map((row, idx) => (
                  <div
                    key={row.label}
                    className={`flex items-center justify-between px-4 py-3 ${
                      idx < section.rows.length - 1
                        ? "border-b border-border/50"
                        : ""
                    }`}
                  >
                    <span className="font-mono text-xs text-muted-foreground/85 tracking-wide">
                      {row.label}
                    </span>
                    <span className="font-mono text-xs font-medium text-foreground/80 tabular-nums">
                      {row.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))
        )}

        {/* Version info */}
        <div className="flex flex-col items-center gap-1 pt-2">
          <span className="font-mono text-[11px] text-muted-foreground/50">
            Coliseum v1.9.0
          </span>
          <span className="font-mono text-[10px] text-yellow-500/40">
            {paperMode ? "Paper Trading Mode" : "Live Trading Mode"}
          </span>
        </div>
      </div>

      <MobileBottomNav />
    </div>
  );
}
