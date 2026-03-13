"use client";

import React from "react";
import { ExternalLink } from "lucide-react";
import { FontSize } from "@/lib/typography";
import { Muted, Base, Strong, Faint } from "@/lib/styles";
import type { ParsedSections, ScoutSection, ResearchSection } from "@/lib/types";

// ---------------------------------------------------------------------------
// Color helpers
// ---------------------------------------------------------------------------

function riskColors(level: string) {
  switch (level.toUpperCase()) {
    case "NEGLIGIBLE":
    case "LOW":
      return {
        text: "text-emerald-400",
        border: "border-emerald-500/30",
        bg: "bg-emerald-500/6",
      };
    case "MODERATE":
      return {
        text: "text-amber-500",
        border: "border-amber-600/20",
        bg: "bg-amber-500/6",
      };
    case "HIGH":
      return {
        text: "text-red-400",
        border: "border-red-500/30",
        bg: "bg-red-500/6",
      };
    default:
      return {
        text: Muted.mutedText,
        border: "border-border",
        bg: "bg-transparent",
      };
  }
}

function flipRiskColors(flip: string) {
  switch (flip) {
    case "NO":
      return { text: "text-emerald-400", border: "border-emerald-500/30", bg: "bg-emerald-500/6" };
    case "YES":
      return { text: "text-red-400", border: "border-red-500/30", bg: "bg-red-500/6" };
    default:
      return { text: "text-amber-500", border: "border-amber-600/20", bg: "bg-amber-500/6" };
  }
}

// ---------------------------------------------------------------------------
// Atoms
// ---------------------------------------------------------------------------

function Pill({
  label,
  value,
  colors,
}: {
  label: string;
  value: string;
  colors: { text: string; border: string; bg: string };
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 ${FontSize.small} font-mono uppercase tracking-wider border rounded px-1.5 py-0.5 ${colors.border} ${colors.bg}`}
    >
      <span className={Muted.mutedText}>{label}</span>
      <span className={`font-bold ${colors.text}`}>{value}</span>
    </span>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className={`${FontSize.small} font-mono uppercase tracking-wider ${Muted.mutedText} mb-1`}>
      {children}
    </p>
  );
}

function SourcePills({ sources }: { sources: string[] }) {
  if (!sources.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {sources.map((url, i) => {
        let hostname = url;
        try {
          hostname = new URL(url).hostname.replace(/^www\./, "");
        } catch {}
        return (
          <a
            key={i}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center gap-1 ${FontSize.small} font-mono border border-border rounded px-1.5 py-0.5 ${Base.foreground} hover:text-foreground hover:border-border/60 transition-colors max-w-[180px] truncate`}
          >
            <ExternalLink className="h-2.5 w-2.5 shrink-0" />
            <span className="truncate">{hostname}</span>
          </a>
        );
      })}
    </div>
  );
}

function EvidenceCard({
  title,
  items,
  variant,
}: {
  title: string;
  items: string[];
  variant: "for" | "against";
}) {
  const borderColor = variant === "for" ? "border-l-amber-500/50" : "border-l-emerald-500/40";
  if (!items.length) return null;
  return (
    <div className={`flex-1 border-l-2 ${borderColor} pl-3 space-y-1`}>
      <SectionLabel>{title}</SectionLabel>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className={`${FontSize.medium} ${Strong.foreground} leading-relaxed`}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Scout Panel
// ---------------------------------------------------------------------------

function ScoutPanel({ scout }: { scout: ScoutSection }) {
  const riskC = riskColors(scout.risk_level);
  const outcomeC = (() => {
    switch (scout.outcome_status) {
      case "CONFIRMED":
        return { text: "text-emerald-400", border: "border-emerald-500/30", bg: "bg-emerald-500/6" };
      case "NEAR-DECIDED":
        return { text: "text-amber-500", border: "border-amber-600/20", bg: "bg-amber-500/6" };
      default:
        return { text: "text-sky-400", border: "border-sky-500/30", bg: "bg-sky-500/6" };
    }
  })();

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`${FontSize.small} font-mono uppercase tracking-wider ${Muted.mutedText}`}>
          SCOUT
        </span>
        {scout.outcome_status && (
          <Pill label="" value={scout.outcome_status} colors={outcomeC} />
        )}
        {scout.risk_level && (
          <Pill label="RISK:" value={scout.risk_level} colors={riskC} />
        )}
      </div>

      {scout.summary && (
        <p className={`${FontSize.large} ${Strong.foreground} leading-relaxed`}>
          {scout.summary}
        </p>
      )}

      {scout.evidence.length > 0 && (
        <div>
          <SectionLabel>Evidence</SectionLabel>
          <ul className="space-y-1">
            {scout.evidence.map((item, i) => (
              <li key={i} className={`${FontSize.medium} ${Strong.foreground} leading-relaxed`}>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {scout.resolution_source && (
        <p className={`${FontSize.medium} ${Muted.foreground} leading-relaxed`}>
          <span className="font-mono uppercase tracking-wider">Resolution:</span>{" "}
          {scout.resolution_source}
        </p>
      )}

      {scout.remaining_risks.length > 0 && (
        <div>
          <SectionLabel>Risks</SectionLabel>
          <ul className="space-y-1">
            {scout.remaining_risks.map((r, i) => (
              <li key={i} className={`${FontSize.medium} ${Muted.amberLabel} leading-relaxed`}>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      <SourcePills sources={scout.sources} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Research Panel
// ---------------------------------------------------------------------------

function ResearchPanel({ research }: { research: ResearchSection }) {
  const flipC = flipRiskColors(research.flip_risk);
  const confColors: Record<string, string> = {
    HIGH: "text-emerald-400",
    MEDIUM: "text-amber-500",
    LOW: "text-red-400",
  };

  return (
    <div className="space-y-3 border-t border-border/40 pt-4">
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`${FontSize.small} font-mono uppercase tracking-wider ${Muted.mutedText}`}>
          RESEARCH
        </span>
        <Pill label="FLIP RISK:" value={research.flip_risk} colors={flipC} />
        {research.confidence && (
          <span className={`${FontSize.small} font-mono uppercase tracking-wider ${confColors[research.confidence] ?? Muted.mutedText}`}>
            CONF: {research.confidence}
          </span>
        )}
      </div>

      {research.event_status && (
        <p className={`${FontSize.medium} ${Strong.foreground} leading-relaxed`}>
          {research.event_status}
        </p>
      )}

      <div className="flex flex-col gap-3 md:flex-row md:gap-4">
        <EvidenceCard
          title="For YES (risks to position)"
          items={research.evidence_for}
          variant="for"
        />
        <EvidenceCard
          title="Against YES"
          items={research.evidence_against}
          variant="against"
        />
      </div>

      {research.resolution_mechanics && (
        <p className={`${FontSize.medium} ${Muted.foreground} leading-relaxed`}>
          <span className="font-mono uppercase tracking-wider">Resolution:</span>{" "}
          {research.resolution_mechanics}
        </p>
      )}

      {research.conclusion && (
        <p className={`${FontSize.medium} ${Strong.foreground} leading-relaxed`}>
          {research.conclusion}
        </p>
      )}

      {research.unconfirmed.length > 0 && (
        <div>
          <SectionLabel>Unconfirmed</SectionLabel>
          <ul className="space-y-1">
            {research.unconfirmed.map((u, i) => (
              <li key={i} className={`${FontSize.medium} ${Muted.amberLabel} leading-relaxed`}>
                {u}
              </li>
            ))}
          </ul>
        </div>
      )}

      <SourcePills sources={research.sources} />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Public export
// ---------------------------------------------------------------------------

export function IntelBrief({ parsed }: { parsed: ParsedSections }) {
  return (
    <div className="space-y-4">
      <ScoutPanel scout={parsed.scout} />
      {parsed.research && <ResearchPanel research={parsed.research} />}
    </div>
  );
}
