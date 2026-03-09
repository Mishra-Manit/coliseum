"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { ChartDataPoint } from "@/lib/types";

interface TooltipPayload {
  value: number;
  payload: ChartDataPoint;
}

interface PnlTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

function PnlTooltip({ active, payload, label }: PnlTooltipProps) {
  if (!active || !payload?.length) return null;
  const pnl = payload[0].value;
  const point = payload[0].payload;

  return (
    <div className="bg-card border border-border rounded-lg p-2.5 shadow-2xl">
      <p className="text-[9px] font-mono text-muted-foreground/60 mb-1.5">{label}</p>
      <span
        className={`text-[13px] font-mono font-semibold tabular-nums ${
          pnl >= 0 ? "text-emerald-400" : "text-red-400"
        }`}
      >
        {pnl >= 0 ? "+" : ""}
        {pnl.toFixed(2)}
      </span>
      <div className="mt-1">
        <span className="text-[9px] font-mono text-muted-foreground/50">
          {point.trades} trade{point.trades !== 1 ? "s" : ""} · {point.wins}W {point.losses}L
        </span>
      </div>
    </div>
  );
}

interface DailyPnlBarsProps {
  data: ChartDataPoint[];
}

export function DailyPnlBars({ data }: DailyPnlBarsProps) {
  const formatDate = (dateStr: string) => {
    const parts = dateStr.split("-");
    return `${parts[1]}/${parts[2]}`;
  };

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-[11px] font-mono text-muted-foreground/40 tracking-[0.12em]">
          NO TRADE DATA YET
        </p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid
          strokeDasharray="0"
          stroke="rgba(46, 42, 64, 0.45)"
          horizontal={true}
          vertical={false}
        />
        <XAxis
          dataKey="date"
          tickFormatter={formatDate}
          tick={{
            fill: "#8e8b98",
            fontSize: 9,
            fontFamily: "var(--font-mono)",
          }}
          axisLine={{ stroke: "#2e2a40" }}
          tickLine={false}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{
            fill: "#8e8b98",
            fontSize: 9,
            fontFamily: "var(--font-mono)",
          }}
          axisLine={false}
          tickLine={false}
          width={54}
          tickFormatter={(v: number) =>
            v >= 0 ? `+$${v.toFixed(0)}` : `-$${Math.abs(v).toFixed(0)}`
          }
        />
        <Tooltip
          content={<PnlTooltip />}
          cursor={{ fill: "rgba(255,255,255,0.018)" }}
        />
        <ReferenceLine y={0} stroke="#2e2a40" strokeWidth={1} />
        <Bar dataKey="pnl" radius={[2, 2, 0, 0]} maxBarSize={40}>
          {data.map((entry, idx) => (
            <Cell
              key={idx}
              fill={entry.pnl >= 0 ? "#16a34a" : "#dc2626"}
              fillOpacity={0.75}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
