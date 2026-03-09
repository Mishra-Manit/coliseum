"use client";

import { Settings } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useConfig } from "@/hooks/use-api";
import { Skeleton } from "@/components/ui/skeleton";

type SettingRow = {
  label: string;
  value: string;
};

type AgentSection = {
  agent: string;
  rows: SettingRow[];
};

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

function buildSections(config: Record<string, unknown>): AgentSection[] {
  const daemon = (config.daemon ?? {}) as Record<string, unknown>;
  const analyst = (config.analyst ?? {}) as Record<string, unknown>;
  const execution = (config.execution ?? {}) as Record<string, unknown>;
  const guardian = (config.guardian ?? {}) as Record<string, unknown>;

  return [
    {
      agent: "DAEMON",
      rows: [
        {
          label: "Pipeline cycle",
          value:
            typeof daemon.heartbeat_interval_minutes === "number"
              ? formatMinutes(daemon.heartbeat_interval_minutes)
              : "—",
        },
        {
          label: "Guardian check interval",
          value:
            typeof daemon.guardian_interval_minutes === "number"
              ? formatMinutes(daemon.guardian_interval_minutes)
              : "—",
        },
        {
          label: "Max consecutive failures",
          value:
            typeof daemon.max_consecutive_failures === "number"
              ? String(daemon.max_consecutive_failures)
              : "—",
        },
      ],
    },
    {
      agent: "ANALYST",
      rows: [
        {
          label: "Max research time",
          value:
            typeof analyst.max_research_time_seconds === "number"
              ? formatSeconds(analyst.max_research_time_seconds)
              : "—",
        },
      ],
    },
    {
      agent: "EXECUTION",
      rows: [
        {
          label: "Order check interval",
          value:
            typeof execution.order_check_interval_seconds === "number"
              ? formatSeconds(execution.order_check_interval_seconds)
              : "—",
        },
        {
          label: "Max order age",
          value:
            typeof execution.max_order_age_minutes === "number"
              ? formatMinutes(execution.max_order_age_minutes)
              : "—",
        },
        {
          label: "Max reprice attempts",
          value:
            typeof execution.max_reprice_attempts === "number"
              ? String(execution.max_reprice_attempts)
              : "—",
        },
      ],
    },
    {
      agent: "GUARDIAN",
      rows: [
        {
          label: "Max hold days",
          value:
            typeof guardian.max_hold_days === "number"
              ? `${guardian.max_hold_days}d`
              : "—",
        },
      ],
    },
  ];
}

function SettingsRow({ label, value }: SettingRow) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-[11px] font-mono text-muted-foreground/70 tracking-wide">
        {label}
      </span>
      <span className="text-[11px] font-mono font-medium text-foreground/80 tabular-nums">
        {value}
      </span>
    </div>
  );
}

function AgentBlock({ agent, rows }: AgentSection) {
  return (
    <div>
      <p className="text-[9px] font-mono font-bold text-muted-foreground/50 tracking-[0.2em] uppercase mb-1">
        {agent}
      </p>
      <div className="divide-y divide-border/50">
        {rows.map((row) => (
          <SettingsRow key={row.label} label={row.label} value={row.value} />
        ))}
      </div>
    </div>
  );
}

function SettingsSkeleton() {
  return (
    <div className="flex flex-col gap-5">
      {[1, 2, 3, 4].map((i) => (
        <div key={i}>
          <Skeleton className="h-2.5 w-12 mb-2" />
          <div className="flex flex-col gap-2">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SettingsModal() {
  const { data: config, isLoading } = useConfig();

  const sections =
    config && !isLoading
      ? buildSections(config as unknown as Record<string, unknown>)
      : [];

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          className="p-1.5 rounded hover:bg-secondary text-muted-foreground/70 hover:text-muted-foreground transition-colors"
          title="Agent settings"
        >
          <Settings className="h-3 w-3" />
        </button>
      </DialogTrigger>
      <DialogContent className="w-80 border border-border rounded-md p-5">
        <DialogHeader className="mb-4">
          <DialogTitle className="text-xs font-mono font-bold tracking-[0.15em] uppercase text-foreground/80">
            Agent time settings
          </DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <SettingsSkeleton />
        ) : (
          <div className="flex flex-col gap-5">
            {sections.map((section) => (
              <AgentBlock
                key={section.agent}
                agent={section.agent}
                rows={section.rows}
              />
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
