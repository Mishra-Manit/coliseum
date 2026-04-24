"use client";

import { useState, useRef, useEffect } from "react";
import { ArrowLeft, Copy, Check, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useOpportunityDetail, usePortfolioState } from "@/hooks/use-api";
import { useTimezone, formatInTz } from "@/lib/timezone-context";
import { stripCitations } from "@/lib/citations";
import { IntelBrief } from "@/components/dashboard/intel-brief";
import type { EnrichedPosition } from "@/lib/types";

interface MobilePositionDetailProps {
  opportunityId: string;
  onBack: () => void;
}

export function MobilePositionDetail({
  opportunityId,
  onBack,
}: MobilePositionDetailProps) {
  const { data, isLoading } = useOpportunityDetail(opportunityId);
  const { data: portfolio } = usePortfolioState();
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

  const openPosition =
    portfolio?.open_positions?.find((p) => p.opportunity_id === opportunityId) ??
    null;

  return (
    <div className="flex flex-col h-[100dvh] bg-background overflow-hidden">
      {/* Nav Header */}
      <div className="shrink-0 flex items-center justify-between h-12 px-5 bg-card border-b border-border">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            aria-label="Back"
            className="text-foreground/80 -ml-1 p-1 rounded active:bg-white/[0.04] transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <span className="font-mono text-[11px] font-bold text-foreground/80 tracking-[0.18em]">
            {openPosition ? "POSITION" : "OPPORTUNITY"}
          </span>
        </div>
        {data && (
          <div className="rounded bg-amber-500/[0.06] border border-amber-500/20 px-2 py-[3px]">
            <span className="font-mono text-[10px] font-medium text-amber-400/80 tracking-[0.12em]">
              {data.summary.status.toUpperCase()}
            </span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto min-h-0 px-5 py-5">
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
            position={openPosition}
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
  position,
  tz,
  copied,
  onCopyTicker,
}: {
  data: NonNullable<ReturnType<typeof useOpportunityDetail>["data"]>;
  position: EnrichedPosition | null;
  tz: "EST" | "PST";
  copied: boolean;
  onCopyTicker: (ticker: string) => void;
}) {
  const { summary, markdown_body, parsed_sections } = data;
  const useStructured =
    parsed_sections !== null &&
    parsed_sections !== undefined &&
    parsed_sections.scout.is_structured === true;

  const strippedMarkdown = useStructured
    ? ""
    : stripCitations(
        markdown_body
          .replace(/^#\s+.+\n?/, "")
          .replace(/^\*\*Event\*\*:.*\n?/m, "")
          .replace(/^\*\*Outcome\*\*:.*\n?/m, "")
          .replace(/^Outcome:.*\n?/m, ""),
      )
        .replace(/^\n+/, "")
        .replace(/\n{3,}/g, "\n\n")
        .trimStart();

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
    <div className="flex flex-col gap-4">
      {/* Title — font-sans, readable */}
      <div className="flex flex-col gap-1">
        <h2 className="text-[17px] font-semibold text-foreground leading-snug font-sans tracking-[-0.01em]">
          {headerTitle}
        </h2>
        {summary.subtitle && (
          <p className="text-[12px] text-muted-foreground/85 font-sans leading-snug">
            {summary.subtitle}
          </p>
        )}
      </div>

      {/* Position Card — only when an open position exists */}
      {position && <PositionCard position={position} />}

      {/* Market meta row */}
      <div className="flex items-start justify-between gap-3">
        <button
          onClick={() => onCopyTicker(summary.market_ticker)}
          className={`inline-flex items-center gap-1.5 font-mono text-[11px] tracking-wider transition-colors min-w-0 ${
            copied ? "text-emerald-400/80" : "text-muted-foreground/85"
          }`}
        >
          {copied ? (
            <Check className="h-3 w-3 shrink-0" />
          ) : (
            <Copy className="h-3 w-3 shrink-0" />
          )}
          <span className="truncate text-left">{summary.market_ticker}</span>
        </button>
        <div className="flex items-center gap-1.5 text-muted-foreground/60 shrink-0">
          <Clock className="h-3 w-3" />
          <span className="font-mono text-[11px] whitespace-nowrap">
            {closeRelativeLabel}
          </span>
        </div>
      </div>

      {/* Price row */}
      <div className="flex items-center gap-2.5 border-t border-border/40 pt-3">
        <span className="font-mono text-[12px] font-semibold text-emerald-400 tabular-nums">
          YES {yesPercent}¢
        </span>
        <span className="font-mono text-[12px] text-muted-foreground/50">/</span>
        <span className="font-mono text-[12px] font-semibold text-red-400 tabular-nums">
          NO {noPercent}¢
        </span>
        <span className="flex-1" />
        <span className="font-mono text-[11px] text-muted-foreground/70 tabular-nums">
          {closeFormatted}
        </span>
      </div>

      {/* Intel body */}
      <div className="pt-1">
        {useStructured && parsed_sections ? (
          <IntelBrief parsed={parsed_sections} />
        ) : strippedMarkdown.trim().length > 0 ? (
          <div className="markdown-body">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {strippedMarkdown}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground/85 font-sans leading-relaxed">
            No analysis available for this opportunity.
          </p>
        )}
      </div>
    </div>
  );
}

function PositionCard({ position }: { position: EnrichedPosition }) {
  const entryC = Math.round(position.average_entry * 100);
  const currentC =
    position.current_price > 0 ? Math.round(position.current_price * 100) : null;
  const isPositive = position.unrealized_pnl >= 0;
  const isYes = position.side === "YES";

  const sideClasses = isYes
    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
    : "bg-red-500/10 border-red-500/30 text-red-400";
  const pnlColor = isPositive ? "text-emerald-400" : "text-red-400";
  const pnlSign = isPositive ? "+" : "";

  return (
    <div className="rounded-lg bg-white/[0.03] border border-white/[0.08] p-4 flex flex-col gap-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={`rounded border px-2 py-[3px] ${sideClasses}`}
          >
            <span className="font-mono text-[10px] font-semibold tracking-wider">
              {position.side}
            </span>
          </div>
          <span className="font-mono text-[11px] text-muted-foreground/85 tabular-nums">
            x{position.contracts} contracts
          </span>
        </div>
        <span
          className={`font-mono text-[20px] font-bold tabular-nums leading-none ${pnlColor}`}
        >
          {pnlSign}${Math.abs(position.unrealized_pnl).toFixed(2)}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 border-t border-white/[0.05] pt-3">
        <MetricCell label="ENTRY" value={`${entryC}¢`} />
        <MetricCell
          label="CURRENT"
          value={currentC !== null ? `${currentC}¢` : "—"}
          align="center"
          tone={currentC !== null ? (isPositive ? "positive" : "negative") : "neutral"}
        />
        <MetricCell
          label="RETURN"
          value={`${pnlSign}${position.pct_change.toFixed(1)}%`}
          align="end"
          tone={isPositive ? "positive" : "negative"}
        />
      </div>
    </div>
  );
}

function MetricCell({
  label,
  value,
  align = "start",
  tone = "neutral",
}: {
  label: string;
  value: string;
  align?: "start" | "center" | "end";
  tone?: "positive" | "negative" | "neutral";
}) {
  const alignClass =
    align === "center"
      ? "items-center text-center"
      : align === "end"
        ? "items-end text-right"
        : "items-start text-left";
  const valueColor =
    tone === "positive"
      ? "text-emerald-400"
      : tone === "negative"
        ? "text-red-400"
        : "text-foreground/85";
  return (
    <div className={`flex flex-col gap-1 ${alignClass}`}>
      <span className="font-mono text-[9px] text-muted-foreground/60 tracking-[0.14em]">
        {label}
      </span>
      <span
        className={`font-mono text-[14px] font-semibold tabular-nums ${valueColor}`}
      >
        {value}
      </span>
    </div>
  );
}
