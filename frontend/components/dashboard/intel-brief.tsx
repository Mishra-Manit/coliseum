"use client";

import React from "react";
import { ExternalLink } from "lucide-react";
import { FontSize } from "@/lib/typography";
import { Muted, Strong } from "@/lib/styles";
import type { ParsedSections } from "@/lib/types";

function stripCitations(text: string): string {
  return text.replace(/\W{0,4}(?:file)?cite\W{0,4}(?:turn\d+\w+\W{0,4})+/g, "").trim();
}

function InlineMarkdown({ text }: { text: string }) {
  const clean = stripCitations(text);
  const parts = clean.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
          return <strong key={i}>{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
          return <em key={i}>{part.slice(1, -1)}</em>;
        }
        return part || null;
      })}
    </>
  );
}

function riskColor(level: string): string {
  switch (level.toUpperCase()) {
    case "NEGLIGIBLE":
    case "LOW":
      return "text-emerald-400";
    case "MODERATE":
      return "text-amber-500";
    case "HIGH":
      return "text-red-400";
    default:
      return Muted.mutedText;
  }
}

function flipRiskColor(flip: string): string {
  switch (flip) {
    case "NO":
      return "text-emerald-400";
    case "YES":
      return "text-red-400";
    default:
      return "text-amber-500";
  }
}

function SectionDivider({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 pt-1">
      <span className={`${FontSize.small} font-mono uppercase tracking-[0.15em] ${Muted.mutedText} shrink-0`}>
        {label}
      </span>
      <div className="flex-1 h-px bg-border/40" />
    </div>
  );
}

function BulletList({
  items,
  className,
}: {
  items: string[];
  className?: string;
}) {
  if (items.length === 0) return null;
  return (
    <ul className={`list-disc list-inside space-y-1 ${className ?? ""}`}>
      {items.map((item, i) => (
        <li key={i} className={`${FontSize.medium} ${Strong.foreground} leading-relaxed`}>
          <InlineMarkdown text={item} />
        </li>
      ))}
    </ul>
  );
}

function SourceLinks({ sources }: { sources: string[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {sources.map((url, i) => {
        let hostname = url;
        try {
          hostname = new URL(url).hostname.replace(/^www\./, "");
        } catch {
          /* keep raw string */
        }
        return (
          <a
            key={i}
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className={`inline-flex items-center gap-1 ${FontSize.small} font-mono border border-border rounded px-1.5 py-0.5 ${Muted.foreground} hover:text-foreground hover:border-border/60 transition-colors max-w-[180px] truncate`}
          >
            <ExternalLink className="h-2.5 w-2.5 shrink-0" />
            <span className="truncate">{hostname}</span>
          </a>
        );
      })}
    </div>
  );
}

function deduplicateStrings(items: string[]): string[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    const normalized = stripCitations(item).toLowerCase().trim();
    if (seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}

export function IntelBrief({ parsed }: { parsed: ParsedSections }) {
  const { scout, research } = parsed;

  const supportingEvidence = deduplicateStrings([
    ...scout.evidence,
    ...(research?.evidence_for ?? []),
  ]);

  const contraryEvidence = deduplicateStrings([
    ...(research?.evidence_against ?? []),
  ]);

  const mergedRisks = deduplicateStrings([
    ...scout.remaining_risks,
    ...(research?.unconfirmed ?? []),
  ]);

  const mergedSources = deduplicateStrings([
    ...scout.sources,
    ...(research?.sources ?? []),
  ]);

  const resolution = research?.resolution_mechanics || scout.resolution_source;
  const conclusion = research?.conclusion || scout.summary;

  return (
    <div className="space-y-4">
      {/* Verdict line */}
      <div className="flex items-center gap-2 flex-wrap">
        {scout.outcome_status && (
          <span className={`${FontSize.small} font-mono font-bold uppercase tracking-wider text-sky-400`}>
            {scout.outcome_status}
          </span>
        )}
        {scout.outcome_status && scout.risk_level && (
          <span className={Muted.mutedText}>/</span>
        )}
        {scout.risk_level && (
          <span className={`${FontSize.small} font-mono uppercase tracking-wider ${riskColor(scout.risk_level)}`}>
            {scout.risk_level} RISK
          </span>
        )}
        {research && (
          <>
            <span className={Muted.mutedText}>/</span>
            <span className={`${FontSize.small} font-mono uppercase tracking-wider`}>
              <span className={Muted.mutedText}>FLIP </span>
              <span className={`font-bold ${flipRiskColor(research.flip_risk)}`}>
                {research.flip_risk}
              </span>
            </span>
          </>
        )}
      </div>

      {/* Summary / Conclusion */}
      {conclusion && (
        <p className={`${FontSize.large} ${Strong.foreground} leading-relaxed`}>
          <InlineMarkdown text={conclusion} />
        </p>
      )}

      {/* Supporting evidence */}
      {supportingEvidence.length > 0 && (
        <div>
          <SectionDivider label="Evidence" />
          <div className="mt-2">
            <BulletList items={supportingEvidence} />
          </div>
        </div>
      )}

      {/* Contrary evidence */}
      {contraryEvidence.length > 0 && (
        <div>
          <SectionDivider label="Against" />
          <div className="mt-2">
            <BulletList
              items={contraryEvidence}
              className="[&_li]:text-red-400/70"
            />
          </div>
        </div>
      )}

      {/* Risks */}
      {mergedRisks.length > 0 && (
        <div>
          <SectionDivider label="Risks" />
          <div className="mt-2">
            <BulletList
              items={mergedRisks}
              className="[&_li]:text-amber-500/70"
            />
          </div>
        </div>
      )}

      {/* Resolution */}
      {resolution && (
        <div>
          <SectionDivider label="Resolution" />
          <p className={`${FontSize.medium} ${Muted.foreground} leading-relaxed mt-2`}>
            <InlineMarkdown text={resolution} />
          </p>
        </div>
      )}

      {/* Sources */}
      {mergedSources.length > 0 && (
        <div>
          <SectionDivider label="Sources" />
          <div className="mt-2">
            <SourceLinks sources={mergedSources} />
          </div>
        </div>
      )}
    </div>
  );
}
