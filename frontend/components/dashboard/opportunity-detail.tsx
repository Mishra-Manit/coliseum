"use client";

import React, { useState, useRef, useEffect } from "react";
import { formatDistanceToNow } from "date-fns";
import { X, Clock, Copy, Check, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useOpportunityDetail } from "@/hooks/use-api";
import { useTimezone, formatInTz } from "@/lib/timezone-context";
import { stripCitations } from "@/lib/citations";
import { FontSize } from "@/lib/typography";
import { Muted, BgTint, BorderTint } from "@/lib/styles";
import { IntelBrief } from "./intel-brief";

interface OpportunityDetailProps {
  opportunityId: string | null;
  onClose: () => void;
}

/** Recursively extract plain text from React children */
function childText(children: React.ReactNode): string {
  if (typeof children === "string") return children;
  if (typeof children === "number") return String(children);
  if (Array.isArray(children)) return children.map(childText).join("");
  if (React.isValidElement(children))
    return childText(
      (children.props as { children?: React.ReactNode }).children
    );
  return "";
}

export function OpportunityDetailView({
  opportunityId,
  onClose,
}: OpportunityDetailProps) {
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
    navigator.clipboard.writeText(ticker)
      .then(() => {
        setCopied(true);
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => setCopied(false), 1500);
      })
      .catch(() => {});
  }

  if (!opportunityId) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${Muted.mutedText} gap-2`}>
        <FileText className="h-7 w-7" />
        <p className={`${FontSize.medium} font-mono tracking-wider`}>
          SELECT OPPORTUNITY
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-5 space-y-4">
        <div className="shimmer h-6 w-3/4 rounded" />
        <div className="shimmer h-4 w-1/2 rounded" />
        <div className="flex gap-3 mt-4">
          <div className="shimmer h-16 flex-1 rounded" />
          <div className="shimmer h-16 flex-1 rounded" />
        </div>
        <div className="shimmer h-px w-full rounded mt-2" />
        <div className="space-y-2">
          <div className="shimmer h-4 w-full rounded" />
          <div className="shimmer h-4 w-5/6 rounded" />
          <div className="shimmer h-4 w-4/5 rounded" />
          <div className="shimmer h-4 w-full rounded" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className={`flex flex-col items-center justify-center h-full ${Muted.mutedText} gap-2`}>
        <p className={`${FontSize.medium} font-mono tracking-wider`}>NOT FOUND</p>
      </div>
    );
  }

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

  const yesPercent = Math.round(summary.yes_price * 100);
  const noPercent = Math.round(summary.no_price * 100);
  const headerTitle = summary.event_title || summary.title;

  const closeDate = summary.close_time ? new Date(summary.close_time) : null;
  const closeFormatted = closeDate ? formatInTz(closeDate, tz) : "N/A";
  const closeRelative = closeDate
    ? formatDistanceToNow(closeDate, { addSuffix: true })
    : "N/A";

  return (
    <div className="flex flex-col h-full">
      {/* Compact header */}
      <div className="shrink-0 px-5 pt-4 pb-3 border-b border-border">
        {/* Top row: status badge + close button */}
        <div className="flex items-center justify-between mb-2">
          <span className={`${FontSize.small} font-mono ${Muted.amberLabel} uppercase tracking-wider border ${BorderTint.amberSelected} ${BgTint.amberBadge} px-1.5 py-0.5 rounded`}>
            {summary.status}
          </span>
          <button
            onClick={onClose}
            aria-label="Close detail"
            className={`p-1 rounded hover:bg-secondary ${Muted.mutedText} hover:text-muted-foreground shrink-0 transition-colors`}
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Title */}
        <div>
          <h2 className="text-[14px] font-semibold text-foreground leading-snug">
            {headerTitle}
          </h2>
          {summary.subtitle ? (
            <p className={`mt-1 ${FontSize.small} ${Muted.mutedText} leading-snug`}>
              {summary.subtitle}
            </p>
          ) : null}
        </div>

        {/* Inline prices + close time */}
        <div className={`flex items-center gap-3 mt-2 ${FontSize.medium} font-mono`}>
          <span className="text-emerald-400 font-semibold tabular-nums">
            YES {yesPercent}c
          </span>
          <span className={Muted.mutedText}>/</span>
          <span className="text-red-400 font-semibold tabular-nums">
            NO {noPercent}c
          </span>
          <span className={`${Muted.mutedText} ml-auto flex items-center gap-1`}>
            <Clock className="h-3 w-3" />
            <span className={`${FontSize.small} tabular-nums`}>
              {closeFormatted}
            </span>
            <span className={`${FontSize.small} ${Muted.mutedText}`}>
              ({closeRelative})
            </span>
          </span>
        </div>

        {/* Ticker -- shown once, copyable */}
        <div className="mt-1.5">
          <button
            onClick={() => handleCopyTicker(summary.market_ticker)}
            className={`inline-flex items-center gap-1 ${FontSize.small} font-mono tracking-wider transition-all duration-150 cursor-pointer ${
              copied ? Muted.emeraldLabel : Muted.mutedText
            } hover:text-muted-foreground`}
          >
            {copied ? (
              <Check className="h-2.5 w-2.5" />
            ) : (
              <Copy className="h-2.5 w-2.5" />
            )}
            {summary.market_ticker}
          </button>
        </div>
      </div>

      {/* Intel body */}
      <div className="flex-1 overflow-y-auto min-h-0 min-w-0">
        <div className="px-5 py-4 min-w-0">
          {useStructured ? (
            <IntelBrief parsed={parsed_sections!} />
          ) : (
            <div className="markdown-body">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                  tr: ({ children, ...props }) => {
                    const cells = React.Children.toArray(children);
                    if (cells.length >= 2 && React.isValidElement(cells[0])) {
                      const label = childText(
                        (cells[0] as React.ReactElement<{ children?: React.ReactNode }>).props.children
                      ).trim();
                      if (label === "Closes" && closeDate) {
                        return (
                          <tr {...props}>
                            {cells[0]}
                            <td className="font-mono tabular-nums">
                              {closeFormatted}
                            </td>
                          </tr>
                        );
                      }
                    }
                    return <tr {...props}>{children}</tr>;
                  },
                }}
              >
                {strippedMarkdown}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
