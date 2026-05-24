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

function buildSections(config: ColiseumConfig): AgentSection[] {
  const llm = config.llm ?? {};
  const scout = config.scout ?? {};
  const daemon = config.daemon ?? {};
  const guardian = config.guardian ?? {};

  const minPrice = typeof scout.min_price === "number" ? scout.min_price : null;
  const maxPrice = typeof scout.max_price === "number" ? scout.max_price : null;
  const priceRange =
    minPrice !== null && maxPrice !== null
      ? `${minPrice}¢ – ${maxPrice}¢`
      : "—";

  return [
    {
      agent: "CONFIG",
      rows: [
        {
          label: "LLM provider",
          value: typeof llm.provider === "string" ? llm.provider : "—",
        },
        {
          label: "Price range",
          value: priceRange,
        },
        {
          label: "Min volume",
          value:
            typeof scout.min_volume === "number"
              ? scout.min_volume.toLocaleString()
              : "—",
        },
        {
          label: "Pipeline cycle",
          value:
            typeof daemon.heartbeat_interval_minutes === "number"
              ? formatMinutes(daemon.heartbeat_interval_minutes)
              : "—",
        },
        {
          label: "Stop window",
          value:
            typeof guardian.window_minutes === "number"
              ? formatMinutes(guardian.window_minutes)
              : "—",
        },
        {
          label: "Stop threshold",
          value:
            typeof guardian.window_threshold_price === "number"
              ? `${Math.round(guardian.window_threshold_price * 100)}¢`
              : "—",
        },
        {
          label: "Max stop spread",
          value:
            typeof guardian.max_stop_spread_cents === "number"
              ? `${guardian.max_stop_spread_cents}¢`
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
