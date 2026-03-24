"use client";

import { useEffect, useState } from "react";
import { Strong, Muted, Faint } from "@/lib/styles";
import { FontSize } from "@/lib/typography";

interface RadialGaugeProps {
  value: number;
  label: string;
  sublabel?: string;
  size?: number;
  strokeWidth?: number;
}

const AMBER = "#d97706";
const TRACK_COLOR = "rgba(255, 255, 255, 0.06)";

export function RadialGauge({
  value,
  label,
  sublabel,
  size = 140,
  strokeWidth = 6,
}: RadialGaugeProps) {
  const [mounted, setMounted] = useState(false);

  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedValue = Math.min(100, Math.max(0, value));
  const targetOffset = circumference - (clampedValue / 100) * circumference;

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative gauge-container" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="transform -rotate-90"
          aria-hidden="true"
        >
          {/* Track circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={TRACK_COLOR}
            strokeWidth={strokeWidth}
          />
          {/* Foreground arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={AMBER}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={mounted ? targetOffset : circumference}
            className="gauge-arc"
            style={{
              transition: mounted
                ? "stroke-dashoffset 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)"
                : "none",
            }}
          />
        </svg>
        {/* Center text overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`text-[28px] font-mono font-bold ${Strong.foreground} tabular-nums leading-none`}>
            {clampedValue.toFixed(1)}%
          </span>
          <span className={`text-[10px] font-mono ${Muted.mutedText} tracking-[0.16em] uppercase mt-1`}>
            {label}
          </span>
        </div>
      </div>
      {sublabel && (
        <span className={`${FontSize.small} font-mono ${Faint.mutedText} tabular-nums tracking-wider`}>
          {sublabel}
        </span>
      )}
    </div>
  );
}
