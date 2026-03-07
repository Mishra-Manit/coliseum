"use client";

import React from "react";
import { formatDistanceToNow } from "date-fns";
import { X, Clock, Target, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useOpportunityDetail } from "@/hooks/use-api";
import { useTimezone, formatInTz } from "@/lib/timezone-context";

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

  if (!opportunityId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground/25 gap-2">
        <FileText className="h-7 w-7" />
        <p className="text-[11px] font-mono tracking-wider">
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
      <div className="flex flex-col items-center justify-center h-full text-muted-foreground/25 gap-2">
        <p className="text-[11px] font-mono tracking-wider">NOT FOUND</p>
      </div>
    );
  }

  const { summary, markdown_body } = data;

  const strippedMarkdown = markdown_body
    .replace(/^#\s+.+\n?/, "")
    .replace(/^\*\*Outcome\*\*:.*\n?/m, "")
    .replace(/^Outcome:.*\n?/m, "")
    .replace(/^\n+/, "")
    .replace(/\n{3,}/g, "\n\n")
    .trimStart();

  const yesPercent = Math.round(summary.yes_price * 100);
  const noPercent = Math.round(summary.no_price * 100);

  const closeDate = summary.close_time ? new Date(summary.close_time) : null;
  const closeFormatted = closeDate ? formatInTz(closeDate, tz) : "N/A";
  const closeRelative = closeDate
    ? formatDistanceToNow(closeDate, { addSuffix: true })
    : "N/A";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="shrink-0 px-5 pt-4 pb-3 border-b border-border">
        <div className="flex items-start justify-between gap-3 mb-2">
          <div className="min-w-0 flex-1">
            {/* Status + action row */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[9px] font-mono text-amber-500/70 uppercase tracking-wider border border-amber-600/20 bg-amber-500/6 px-1.5 py-0.5 rounded">
                {summary.status}
              </span>
              {summary.action && (
                <span
                  className={`text-[9px] font-mono font-bold uppercase tracking-wider ${
                    summary.action.includes("YES")
                      ? "text-emerald-400"
                      : "text-red-400"
                  }`}
                >
                  {summary.action}
                </span>
              )}
            </div>

            <h2 className="text-[14px] font-semibold text-foreground leading-snug">
              {summary.title}
            </h2>
            {summary.subtitle && (
              <p className="text-[11px] text-muted-foreground/60 mt-1 leading-relaxed">
                {summary.subtitle}
              </p>
            )}
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-secondary text-muted-foreground/40 hover:text-muted-foreground shrink-0 transition-colors"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Price levels */}
        <div className="grid grid-cols-2 gap-2 mt-3">
          <div className="px-3 py-2 rounded border border-emerald-500/12 bg-emerald-500/4">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-mono text-emerald-400/60 uppercase tracking-wider">
                YES
              </span>
              <span className="text-[18px] font-mono font-bold text-emerald-400 tabular-nums leading-none">
                {yesPercent}c
              </span>
            </div>
            <div className="prob-bar-track mt-2">
              <div
                className="prob-bar-yes"
                style={{ width: `${yesPercent}%` }}
              />
            </div>
          </div>
          <div className="px-3 py-2 rounded border border-red-500/12 bg-red-500/4">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-mono text-red-400/60 uppercase tracking-wider">
                NO
              </span>
              <span className="text-[18px] font-mono font-bold text-red-400 tabular-nums leading-none">
                {noPercent}c
              </span>
            </div>
            <div className="prob-bar-track mt-2">
              <div
                className="prob-bar-yes"
                style={{
                  width: `${noPercent}%`,
                  background: "linear-gradient(90deg, #dc2626, #f87171)",
                }}
              />
            </div>
          </div>
        </div>

        {/* Meta row */}
        <div className="flex items-center gap-4 mt-2.5 text-[10px] font-mono text-muted-foreground/35">
          <span className="flex items-center gap-1" title={closeFormatted}>
            <Clock className="h-3 w-3" />
            {closeFormatted}
          </span>
          <span className="text-muted-foreground/20">·</span>
          <span className="text-muted-foreground/25">{closeRelative}</span>
          <span className="flex items-center gap-1 ml-auto">
            <Target className="h-3 w-3" />
            {summary.market_ticker}
          </span>
        </div>
      </div>

      {/* Markdown body */}
      <div className="flex-1 overflow-y-auto min-h-0 min-w-0">
        <div className="px-5 py-4 markdown-body min-w-0">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
              tr: ({ children, ...props }) => {
                // Intercept the "Closes" row and replace its value with a
                // timezone-aware formatted time derived from summary.close_time
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
      </div>
    </div>
  );
}
