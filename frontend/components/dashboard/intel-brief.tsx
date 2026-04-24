"use client";

import React from "react";
import { ExternalLink } from "lucide-react";
import { FontSize } from "@/lib/typography";
import { Muted, Strong } from "@/lib/styles";
import type { ParsedSections } from "@/lib/types";

function stripCitations(text: string): string {
  // Strip OpenAI `cite…turnXfileY` tokens
  let out = text.replace(/\W{0,4}(?:file)?cite\W{0,4}(?:turn\d+\w+\W{0,4})+/g, "");
  // Strip inline `[hostname.tld]` citation markers (e.g. `[cmegroup.com]`, `[kalshi.com]`)
  out = out.replace(/\s*\[(?:[a-z0-9-]+\.)+[a-z]{2,}\]/gi, "");
  // Collapse stray double spaces left behind
  return out.replace(/\s{2,}/g, " ").trim();
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
  dotClass = "bg-muted-foreground/50",
}: {
  items: string[];
  dotClass?: string;
}) {
  if (items.length === 0) return null;
  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex gap-2.5 text-[13.5px] text-foreground/85 leading-relaxed font-sans">
          <span
            className={`mt-[9px] h-1 w-1 rounded-full shrink-0 ${dotClass}`}
            aria-hidden="true"
          />
          <span className="min-w-0">
            <InlineMarkdown text={item} />
          </span>
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

function TldrBanner({ decision, tldr }: { decision: string; tldr: string }) {
  const isExecute = decision.startsWith("EXECUTE");
  const accentBorder = isExecute ? "border-emerald-500" : "border-red-500";
  const accentText = isExecute ? "text-emerald-400" : "text-red-400";

  const DECISION_LABELS: Record<string, string> = {
    REJECT: "REJECTED",
    EXECUTE_BUY_YES: "EXECUTED \u00B7 BUY YES",
    EXECUTE_BUY_NO: "EXECUTED \u00B7 BUY NO",
  };
  const decisionLabel = DECISION_LABELS[decision] ?? "UNKNOWN";

  return (
    <div>
      <SectionDivider label="TLDR" />
      <div className={`mt-2 border-l-2 ${accentBorder} bg-white/[0.02] rounded-r px-3.5 py-3`}>
        <span className={`text-[11px] font-mono font-bold uppercase tracking-[0.14em] ${accentText}`}>
          {decisionLabel}
        </span>
        <p className="text-[13.5px] text-foreground/90 leading-relaxed mt-1.5 font-sans">
          {stripCitations(tldr)}
        </p>
      </div>
    </div>
  );
}


export function IntelBrief({ parsed }: { parsed: ParsedSections }) {
  const { scout, research, trader } = parsed;

  const supportingEvidence = deduplicateStrings([
    ...scout.evidence,
    ...(research?.evidence_for ?? []),
  ]);

  const contraryEvidence = deduplicateStrings(research?.evidence_against ?? []);

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
      {/* TLDR verdict banner */}
      {trader && <TldrBanner decision={trader.decision} tldr={trader.tldr} />}

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

      {/* Summary / Conclusion — long-form, font-sans for readability */}
      {conclusion && (
        <p className="text-[14px] text-foreground/90 leading-[1.65] font-sans">
          <InlineMarkdown text={conclusion} />
        </p>
      )}

      {/* Supporting evidence */}
      {supportingEvidence.length > 0 && (
        <div>
          <SectionDivider label="Evidence" />
          <div className="mt-2">
            <BulletList items={supportingEvidence} dotClass="bg-emerald-400/70" />
          </div>
        </div>
      )}

      {/* Contrary evidence */}
      {contraryEvidence.length > 0 && (
        <div>
          <SectionDivider label="Against" />
          <div className="mt-2">
            <BulletList items={contraryEvidence} dotClass="bg-red-400" />
          </div>
        </div>
      )}

      {/* Risks */}
      {mergedRisks.length > 0 && (
        <div>
          <SectionDivider label="Risks" />
          <div className="mt-2">
            <BulletList items={mergedRisks} dotClass="bg-amber-400" />
          </div>
        </div>
      )}

      {/* Resolution */}
      {resolution && (
        <div>
          <SectionDivider label="Resolution" />
          <p className="text-[13.5px] text-foreground/75 leading-relaxed mt-2 font-sans">
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
