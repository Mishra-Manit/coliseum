/**
 * Two-tier font size system for the Coliseum dashboard.
 *
 * small  — labels, captions, metadata, status badges, secondary info
 * medium — primary values, tickers, body content in panels
 *
 * Display-level numbers (NAV, win counts, YES/NO prices) and headings
 * are intentional hierarchy markers and are not governed by this enum.
 */
export const FontSize = {
  small: "text-[11px]",
  medium: "text-[12px]",
  large: "text-[13px]",
} as const;

export type FontSizeKey = keyof typeof FontSize;
