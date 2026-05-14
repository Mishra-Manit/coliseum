"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { FontSize } from "@/lib/typography";
import { Muted } from "@/lib/styles";

const THRESHOLDS = [
  { afterS: 60, label: "~15 seconds remaining" },
  { afterS: 45, label: "~30 seconds remaining" },
  { afterS: 0, label: "~75 seconds remaining" },
] as const;

function getLabel(elapsed: number): string {
  for (const t of THRESHOLDS) {
    if (elapsed >= t.afterS) return t.label;
  }
  return THRESHOLDS[THRESHOLDS.length - 1].label;
}

export function VideoExportProgress() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex items-center gap-2">
      <Loader2 className="h-3 w-3 animate-spin text-amber-500/60" />
      <span
        className={`${FontSize.small} font-mono ${Muted.mutedText} tracking-[0.06em] whitespace-nowrap`}
      >
        {getLabel(elapsed)}
      </span>
    </div>
  );
}
