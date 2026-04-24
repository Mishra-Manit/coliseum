/**
 * Remove inline citation markers from LLM-generated text.
 *
 * Handles two flavors:
 *   1. OpenAI `cite…turnXfileY` tokens (sometimes wrapped in non-word chars)
 *   2. `[hostname.tld]` bracket tokens (e.g. `[cmegroup.com]`, `[kalshi.com]`)
 */
export function stripCitations(text: string): string {
  let out = text.replace(
    /\W{0,4}(?:file)?cite\W{0,4}(?:turn\d+\w+\W{0,4})+/g,
    "",
  );
  out = out.replace(/[ \t]*\[(?:[a-z0-9-]+\.)+[a-z]{2,}\]/gi, "");
  // Collapse runs of spaces/tabs only — newlines must be preserved so
  // markdown paragraph structure survives.
  return out.replace(/[ \t]{2,}/g, " ").trim();
}
