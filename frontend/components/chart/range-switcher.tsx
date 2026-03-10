"use client";

import type { Interval } from "@/lib/chart-utils";
import { FontSize } from "@/lib/typography";

const INTERVALS: Interval[] = ["1D", "1W", "1M"];

interface RangeSwitcherProps {
  value: Interval;
  onChange: (interval: Interval) => void;
}

export function RangeSwitcher({ value, onChange }: RangeSwitcherProps) {
  return (
    <div className="flex items-center border border-border rounded overflow-hidden">
      {INTERVALS.map((interval) => (
        <button
          key={interval}
          onClick={() => onChange(interval)}
          className={`px-2.5 py-1 ${FontSize.small} font-mono tracking-[0.1em] transition-colors border-r border-border last:border-r-0 ${
            value === interval
              ? "bg-primary/15 text-primary"
              : "text-muted-foreground/60 hover:text-muted-foreground/70"
          }`}
        >
          {interval}
        </button>
      ))}
    </div>
  );
}
