"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { ChartDataPoint } from "@/lib/types";

interface TooltipPayload {
  payload: ChartDataPoint;
  value: number;
}

interface NavTooltipProps {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}

function NavTooltip({ active, payload, label }: NavTooltipProps) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;

  return (
    <div className="bg-card border border-border rounded-lg p-3 shadow-2xl">
      <p className="text-[9px] font-mono text-muted-foreground/60 tracking-[0.1em] uppercase mb-2.5">
        {label}
      </p>
      <div className="flex flex-col gap-1.5">
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] font-mono text-muted-foreground/60 w-[68px]">CUMUL P&L</span>
          <span
            className={`text-[13px] font-mono font-semibold tabular-nums ${
              point.cumulative_pnl >= 0 ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {point.cumulative_pnl >= 0 ? "+" : ""}
            {point.cumulative_pnl.toFixed(2)}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] font-mono text-muted-foreground/60 w-[68px]">DAY P&L</span>
          <span
            className={`text-[11px] font-mono tabular-nums ${
              point.pnl >= 0 ? "text-emerald-400/80" : "text-red-400/80"
            }`}
          >
            {point.pnl >= 0 ? "+" : ""}
            {point.pnl.toFixed(2)}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] font-mono text-muted-foreground/60 w-[68px]">NAV</span>
          <span className="text-[11px] font-mono text-foreground/70 tabular-nums">
            ${point.nav.toFixed(2)}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] font-mono text-muted-foreground/60 w-[68px]">TRADES</span>
          <span className="text-[11px] font-mono text-muted-foreground/60 tabular-nums">
            {point.trades}
          </span>
        </div>
      </div>
    </div>
  );
}

interface PortfolioNavChartProps {
  data: ChartDataPoint[];
}

export function PortfolioNavChart({ data }: PortfolioNavChartProps) {
  const lastPoint = data[data.length - 1];
  const isPositive = !lastPoint || lastPoint.cumulative_pnl >= 0;
  const lineColor = isPositive ? "#16a34a" : "#dc2626";
  const gradientId = "navGradient";

  const formatDate = (dateStr: string) => {
    const parts = dateStr.split("-");
    return `${parts[1]}/${parts[2]}`;
  };

  const formatY = (val: number) =>
    val >= 0 ? `+$${val.toFixed(0)}` : `-$${Math.abs(val).toFixed(0)}`;

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
      <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={lineColor} stopOpacity={0.18} />
            <stop offset="95%" stopColor={lineColor} stopOpacity={0} />
          </linearGradient>
        </defs>
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
          tickFormatter={formatY}
          tick={{
            fill: "#8e8b98",
            fontSize: 9,
            fontFamily: "var(--font-mono)",
          }}
          axisLine={false}
          tickLine={false}
          width={58}
        />
        <Tooltip
          content={<NavTooltip />}
          cursor={{ stroke: "#d97706", strokeWidth: 1, strokeDasharray: "3 3" }}
        />
        <ReferenceLine y={0} stroke="#2e2a40" strokeWidth={1} />
        <Area
          type="monotone"
          dataKey="cumulative_pnl"
          stroke={lineColor}
          strokeWidth={1.5}
          fill={`url(#${gradientId})`}
          dot={false}
          activeDot={{
            r: 3,
            fill: lineColor,
            stroke: "#07060a",
            strokeWidth: 2,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
