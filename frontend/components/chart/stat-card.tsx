"use client";

interface StatCardProps {
  value: string;
  label: string;
  trend?: "positive" | "negative" | "neutral";
}

export function StatCard({ value, label, trend = "neutral" }: StatCardProps) {
  const valueColor =
    trend === "positive"
      ? "text-emerald-400"
      : trend === "negative"
        ? "text-red-400"
        : "text-foreground/90";

  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-lg p-3 flex flex-col gap-1 hover:bg-white/[0.05] transition-colors stat-card-glow">
      <span className={`text-[18px] font-mono font-bold tabular-nums leading-none ${valueColor}`}>
        {value}
      </span>
      <span className="text-[11px] font-mono text-muted-foreground/70 uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
