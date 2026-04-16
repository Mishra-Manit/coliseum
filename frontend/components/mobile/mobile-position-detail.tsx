"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowLeft, Copy, Check, Clock, ExternalLink } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useOpportunityDetail } from "@/hooks/use-api";
import { useTimezone, formatInTz } from "@/lib/timezone-context";
import { MobileBottomNav } from "./mobile-bottom-nav";
import { IntelBrief } from "@/components/dashboard/intel-brief";
import { FontSize } from "@/lib/typography";
import { Muted, Strong, BgTint, BorderTint } from "@/lib/styles";

interface MobilePositionDetailProps {
  opportunityId: string;
  onBack: () => void;
}

export function MobilePositionDetail({
  opportunityId,
  onBack,
}: MobilePositionDetailProps) {
  const { data, isLoading } = useOpportunityDetail(opportunityId);
  const { tz } = useTimezone();
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  function handleCopyTicker(ticker: string) {
    navigator.clipboard
      .writeText(ticker)
      .then(() => {
        setCopied(true);
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => setCopied(false), 1500);
      })
      .catch(() => {});
  }

  return (
    <div className="flex flex-col h-[100dvh] bg-background overflow-hidden">
      {/* Nav Header */}
      <div className="shrink-0 flex items-center justify-between h-12 px-5 bg-card border-b border-border">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="text-foreground/80">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <span className="font-mono text-xs font-bold text-foreground/80 tracking-[0.18em]">
            POSITION
          </span>
        </div>
        {data && (
          <div className="rounded bg-[#d9770610] border border-[#d9770633] px-2 py-[3px]">
            <span className="font-mono text-[10px] font-medium text-amber-500/70 tracking-[0.12em]">
              {data.summary.status.toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0 px-5 py-4">
        {isLoading ? (
          <div className="space-y-3">
            <div className="shimmer h-5 w-3/4 rounded" />
            <div className="shimmer h-4 w-1/2 rounded" />
            <div className="shimmer h-24 w-full rounded-lg" />
            <div className="shimmer h-3 w-full rounded" />
            <div className="shimmer h-20 w-full rounded" />
          </div>
        ) : !data ? (
          <div className="flex items-center justify-center h-40 text-muted-foreground">
            <p className="font-mono text-xs tracking-wider">NOT FOUND</p>
          </div>
        ) : (
          <DetailContent
            data={data}
            tz={tz}
            copied={copied}
            onCopyTicker={handleCopyTicker}
          />
        )}
      </div>
    </div>
  );
}

function DetailContent({
  data,
  tz,
  copied,
  onCopyTicker,
}: {
  data: NonNullable<ReturnType<typeof useOpportunityDetail>["data"]>;
  tz: "EST" | "PST";
  copied: boolean;
  onCopyTicker: (ticker: string) => void;
}) {
  const { summary, parsed_sections } = data;
  const useStructured =
    parsed_sections !== null &&
    parsed_sections !== undefined &&
    parsed_sections.scout.is_structured === true;

  const headerTitle = summary.event_title || summary.title;
  const yesPercent = Math.round(summary.yes_price * 100);
  const noPercent = Math.round(summary.no_price * 100);
  const closeDate = summary.close_time ? new Date(summary.close_time) : null;
  const closeFormatted = closeDate ? formatInTz(closeDate, tz) : "N/A";
  const closeRelative = closeDate
    ? formatDistanceToNow(closeDate, { addSuffix: true })
    : "";
  const isFuture = closeDate ? closeDate.getTime() > Date.now() : false;
  const closeRelativeLabel = closeRelative
    ? isFuture
      ? closeRelative.startsWith("in ")
        ? closeRelative
        : `in ${closeRelative}`
      : closeRelative
    : "";

  return (
    <div className="flex flex-col gap-3.5">
      {/* Title */}
      <h2 className="text-base font-semibold text-foreground leading-snug font-sans">
        {headerTitle}
      </h2>
      {summary.subtitle && (
        <p className="text-[11px] text-muted-foreground/85 font-sans -mt-1">
          {summary.subtitle}
        </p>
      )}

      {/* Position Card */}
      <div className="rounded-lg bg-white/[0.03] border border-white/[0.08] p-3.5 flex flex-col gap-3">
        {/* Row 1: badge + contracts + PnL */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="rounded bg-emerald-500/10 border border-emerald-500/30 px-2 py-[3px]">
              <span className="font-mono text-[10px] font-semibold text-emerald-400 tracking-wider">
                YES
              </span>
            </div>
            <span className="font-mono text-[11px] text-muted-foreground/85">
              x12 contracts
            </span>
          </div>
          <span className="font-mono text-xl font-bold text-emerald-400 tabular-nums">
            +$3.24
          </span>
        </div>
        {/* Row 2: entry / current / return */}
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-0.5">
            <span className="font-mono text-[9px] text-muted-foreground/50 tracking-[0.12em]">
              ENTRY
            </span>
            <span className="font-mono text-sm font-semibold text-foreground/80 tabular-nums">
              67c
            </span>
          </div>
          <div className="flex flex-col items-center gap-0.5">
            <span className="font-mono text-[9px] text-muted-foreground/50 tracking-[0.12em]">
              CURRENT
            </span>
            <span className="font-mono text-sm font-semibold text-emerald-400 tabular-nums">
              94c
            </span>
          </div>
          <div className="flex flex-col items-end gap-0.5">
            <span className="font-mono text-[9px] text-muted-foreground/50 tracking-[0.12em]">
              RETURN
            </span>
            <span className="font-mono text-sm font-semibold text-emerald-400 tabular-nums">
              +40.3%
            </span>
          </div>
        </div>
      </div>

      {/* Ticker row */}
      <div className="flex items-start justify-between gap-3">
        <button
          onClick={() => onCopyTicker(summary.market_ticker)}
          className={`inline-flex items-center gap-1 font-mono text-[11px] tracking-wider transition-colors min-w-0 ${
            copied ? "text-emerald-400/70" : "text-muted-foreground/85"
          }`}
        >
          {copied ? (
            <Check className="h-2.5 w-2.5 shrink-0" />
          ) : (
            <Copy className="h-2.5 w-2.5 shrink-0" />
          )}
          <span className="truncate text-left">{summary.market_ticker}</span>
        </button>
        <div className="flex items-center gap-1.5 text-muted-foreground/60 shrink-0">
          <Clock className="h-[11px] w-[11px]" />
          <span className="font-mono text-[11px] whitespace-nowrap">
            {closeRelativeLabel}
          </span>
        </div>
      </div>

      {/* Price row */}
      <div className="flex items-center gap-2.5">
        <span className="font-mono text-xs font-semibold text-emerald-400 tabular-nums">
          YES {yesPercent}c
        </span>
        <span className="font-mono text-xs text-muted-foreground/85">/</span>
        <span className="font-mono text-xs font-semibold text-red-400 tabular-nums">
          NO {noPercent}c
        </span>
        <span className="flex-1" />
        <span className="font-mono text-[11px] text-muted-foreground/85">
          {closeFormatted}
        </span>
      </div>

      {/* Intel body */}
      {useStructured && parsed_sections ? (
        <IntelBrief parsed={parsed_sections} />
      ) : (
        <div className="markdown-body text-sm">
          <p className="text-muted-foreground/85">
            No structured analysis available for this opportunity.
          </p>
        </div>
      )}
    </div>
  );
}
