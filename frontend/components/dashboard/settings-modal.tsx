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
import type { ColiseumConfig } from "@/lib/types";
import { Skeleton } from "@/components/ui/skeleton";
import { useTimezone, type Timezone } from "@/lib/timezone-context";
import { FontSize } from "@/lib/typography";
import { Muted, Base, Ghost } from "@/lib/styles";

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

function buildSections(config: ColiseumConfig): AgentSection[] {
  const daemon = config.daemon ?? {};
  const analyst = config.analyst ?? {};
  const execution = config.execution ?? {};
  const guardian = config.guardian ?? {};

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
          label: "Stop-loss threshold",
          value:
            typeof guardian.stop_loss_price === "number"
              ? `${Math.round(guardian.stop_loss_price * 100)}¢`
              : "—",
        },
      ],
    },
  ];
}

function SettingsRow({ label, value }: SettingRow) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className={`text-[11px] font-mono ${Muted.mutedText} tracking-wide`}>
        {label}
      </span>
      <span className={`text-[11px] font-mono font-medium ${Base.foreground} tabular-nums`}>
        {value}
      </span>
    </div>
  );
}

function AgentBlock({ agent, rows }: AgentSection) {
  return (
    <div>
      <p className={`text-[9px] font-mono font-bold ${Ghost.mutedText} tracking-[0.2em] uppercase mb-1`}>
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

function TzSelector({
  tz,
  setTz,
}: {
  tz: Timezone;
  setTz: (tz: Timezone) => void;
}) {
  return (
    <div className="flex items-center border border-border rounded overflow-hidden">
      {(["EST", "PST"] as Timezone[]).map((option) => (
        <button
          key={option}
          onClick={() => setTz(option)}
          className={`px-2.5 py-1 ${FontSize.small} font-mono tracking-wider transition-colors ${
            tz === option
              ? "bg-primary/15 text-primary border-r border-border last:border-r-0"
              : `${Muted.mutedText} hover:text-muted-foreground/70 border-r border-border last:border-r-0`
          }`}
        >
          {option}
        </button>
      ))}
    </div>
  );
}

export function SettingsModal() {
  const { data: config, isLoading } = useConfig();
  const { tz, setTz } = useTimezone();

  const sections =
    config && !isLoading
      ? buildSections(config)
      : [];

  return (
    <Dialog>
      <DialogTrigger asChild>
        <button
          className={`p-1.5 rounded hover:bg-secondary ${Muted.mutedText} hover:text-muted-foreground transition-colors`}
          title="Settings"
        >
          <Settings className="h-3 w-3" />
        </button>
      </DialogTrigger>
      <DialogContent className="w-80 border border-border rounded-md p-5">
        <DialogHeader className="mb-4">
          <DialogTitle className={`text-xs font-mono font-bold tracking-[0.15em] uppercase ${Base.foreground}`}>
            Settings
          </DialogTitle>
        </DialogHeader>

        {/* Timezone */}
        <div className="mb-5">
          <p className={`text-[9px] font-mono font-bold ${Ghost.mutedText} tracking-[0.2em] uppercase mb-2`}>
            TIMEZONE
          </p>
          <TzSelector tz={tz} setTz={setTz} />
        </div>

        {/* Agent timings */}
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
