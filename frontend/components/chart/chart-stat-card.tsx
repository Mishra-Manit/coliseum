"use client";

interface ChartStatCardProps {
  label: string;
  value: string;
  subValue?: string;
  trend?: "positive" | "negative" | "neutral";
}

export function ChartStatCard({
  label,
  value,
  subValue,
  trend = "neutral",
}: ChartStatCardProps) {
  const valueClass =
    trend === "positive"
      ? "text-emerald-400"
      : trend === "negative"
        ? "text-red-400"
        : "text-foreground/90";

  return (
    <div className="bg-card/50 border border-border rounded-lg p-4 glow-amber-hover flex flex-col gap-1.5">
      <span className="text-[9px] font-mono text-muted-foreground/60 tracking-[0.14em] uppercase">
        {label}
      </span>
      <span className={`text-[18px] font-mono font-bold tabular-nums leading-none ${valueClass}`}>
        {value}
      </span>
      {subValue && (
        <span className="text-[9px] font-mono text-muted-foreground/45 tabular-nums">
          {subValue}
        </span>
      )}
    </div>
  );
}
