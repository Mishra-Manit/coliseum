/**
 * Centralized opacity system for the Coliseum dashboard.
 *
 * Elements sharing the same opacity level are grouped together.
 * To change every element at a given level, update the string
 * values in the corresponding group — one edit, global effect.
 *
 * Muted  — secondary text: labels, metadata, icons, muted info (/85)
 * Base   — primary content: values, card backgrounds, status colors (/80)
 * Faint  — tertiary: charts return pct, nav inactive links (/60)
 * Ghost  — very muted: agent section headers (/50)
 * BgTint   — colored backgrounds, grouped by opacity level
 * BorderTint — colored borders, grouped by opacity level
 */

/** /85 — secondary text, labels, muted foreground, icons */
export const Muted = {
  mutedText:           "text-muted-foreground/85",
  mutedTextHover:      "hover:text-muted-foreground/85",
  mutedTextGroupHover: "group-hover:text-muted-foreground/85",
  foreground:          "text-foreground/70",
  emeraldLabel:        "text-emerald-400/70",
  redLabel:            "text-red-400/70",
  amberLabel:          "text-amber-500/70",
  amberWinRate:        "text-amber-400/70",
  skyIcon:             "text-sky-500/70",
  emeraldIcon:         "text-emerald-500/70",
  redIcon:             "text-red-500/70",
  yellowBadge:         "text-yellow-500/70",
} as const;

/** /80 — primary values, card backgrounds, status colors */
export const Base = {
  foreground:     "text-foreground/80",
  card:           "bg-card/80",
  secondary:      "bg-secondary/80",
  yellowStatus:   "text-yellow-500/80",
  skyStatus:      "text-sky-400/80",
  emeraldStatus:  "text-emerald-400/80",
  violetStatus:   "text-violet-400/80",
} as const;

/** /90 — hover/active states, high-contrast foreground */
export const Strong = {
  foreground:           "text-foreground/90",
  foregroundGroupHover: "group-hover:text-foreground/90",
} as const;

/** /75 — intermediate opacity: unselected opportunity titles */
export const Soft = {
  foreground: "text-foreground/75",
} as const;

/** /60 — tertiary elements, inactive nav, chart annotations */
export const Faint = {
  mutedText:    "text-muted-foreground/60",
  foreground:   "text-foreground/60",
  opacityClass: "opacity-60",
} as const;

/** /50 — very muted: agent section labels, placeholder states */
export const Ghost = {
  mutedText: "text-muted-foreground/50",
} as const;

/**
 * Colored background tints, organized by opacity level.
 *
 * /4  — price outcome boxes (YES/NO), clickable row hover
 * /5  — subtle hover backgrounds, win/loss stat boxes
 * /6  — status badge fills
 * /8  — mode badge fills (PAPER / LIVE)
 * /10 — win-rate badge backgrounds, icon backgrounds
 * /50 — ledger type indicator bars
 */
export const BgTint = {
  // /4 — price boxes and row hover
  yesBox:             "bg-emerald-500/4",
  noBox:              "bg-red-500/4",
  amberRowHover:      "bg-amber-500/4",
  // hover state versions (must be full strings for Tailwind scanning)
  amberRowHoverState: "hover:bg-amber-500/4",
  amberHoverState:    "hover:bg-amber-500/5",
  // /5 — subtle hover backgrounds
  amberHover:         "bg-amber-500/5",
  emeraldBox:    "bg-emerald-500/5",
  redBox:        "bg-red-500/5",
  // /6 — status badge fill
  amberBadge:    "bg-amber-500/6",
  // /8 — navbar mode badge fills
  paperBadge:    "bg-yellow-600/8",
  liveBadge:     "bg-emerald-600/8",
  // /10 — win-rate badges and icon backgrounds
  winBg:         "bg-emerald-500/10",
  lossBg:        "bg-red-500/10",
  amberRateBg:   "bg-amber-500/10",
  skyIconBg:     "bg-sky-500/10",
  // /50 — ledger indicator bars
  buyBar:        "bg-sky-500/50",
  winBar:        "bg-emerald-500/50",
  lossBar:       "bg-red-500/50",
} as const;

/**
 * Colored border tints, organized by opacity level.
 *
 * /10 — win/loss stat panels
 * /12 — price outcome boxes
 * /20 — selected opportunity row, status badge border
 * /25 — navbar mode badge borders
 * /30 — account position badges
 * /50 — table row dividers
 */
export const BorderTint = {
  // /10 — win/loss panels
  winPanel:      "border-emerald-500/10",
  lossPanel:     "border-red-500/10",
  // /12 — price boxes
  yesBox:        "border-emerald-500/12",
  noBox:         "border-red-500/12",
  // /20 — selected row / status badge
  amberSelected:      "border-amber-600/20",
  amberSelectedHover: "hover:border-amber-600/20",
  // /25 — navbar mode badge borders
  paperBadge:    "border-yellow-600/25",
  liveBadge:     "border-emerald-600/25",
  // /30 — account position badges
  yesBadge:      "border-emerald-500/30",
  noBadge:       "border-red-500/30",
  amberBadge:    "border-amber-500/30",
  // /50 — table row dividers
  tableRow:      "border-border/50",
} as const;
