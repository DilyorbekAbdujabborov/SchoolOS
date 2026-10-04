/**
 * The app's semantic colour vocabulary.
 *
 * Blue is the brand accent and nothing else: it marks the primary action, the
 * active nav item and a "primary metric". Every other colour is rationed by
 * *what the data means*, so the same word is always the same hue everywhere —
 * a card, a badge, a chart bar and a status dot all resolve through here.
 *
 *   brand   — identity, primary action, the metric you lead with
 *   ember  — secondary/compared metric, progression, "your" personal data
 *   emerald — good, present, completed, positive growth
 *   amber   — attention, pending, late, warning
 *   rose    — bad, absent, failed, destructive
 *   slate   — neutral, inactive, historical
 */
export type Tone = "brand" | "ember" | "emerald" | "amber" | "orange" | "rose" | "slate";

/** Small filled pill: icon/chip/badge backgrounds and text on them. */
export const TONE_CHIP: Record<Tone, string> = {
  brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/15 dark:text-brand-300",
  ember: "bg-ember-50 text-ember-700 dark:bg-ember-500/15 dark:text-ember-300",
  emerald: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
  amber: "bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-300",
  orange: "bg-orange-50 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
  rose: "bg-rose-50 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
  slate: "bg-surface-raised text-ink-muted",
};

/** Solid dot: status indicators, legend swatches, chart accents. */
export const TONE_DOT: Record<Tone, string> = {
  brand: "bg-brand-500",
  ember: "bg-ember-500",
  emerald: "bg-emerald-500",
  amber: "bg-amber-500",
  orange: "bg-orange-500",
  rose: "bg-rose-500",
  slate: "bg-ink-subtle",
};

/** Translucent hue fill for icon wells — pairs with `TONE_TEXT` on top. */
export const TONE_WELL: Record<Tone, string> = {
  brand: "bg-brand-500/10",
  ember: "bg-ember-500/10",
  emerald: "bg-emerald-500/10",
  amber: "bg-amber-500/12",
  orange: "bg-orange-500/12",
  rose: "bg-rose-500/10",
  slate: "bg-surface-raised",
};

/** Text-only accent, for numbers and inline emphasis. */
export const TONE_TEXT: Record<Tone, string> = {
  brand: "text-brand-600 dark:text-brand-400",
  ember: "text-ember-600 dark:text-ember-400",
  emerald: "text-emerald-600 dark:text-emerald-400",
  amber: "text-amber-600 dark:text-amber-400",
  orange: "text-orange-600 dark:text-orange-400",
  rose: "text-rose-600 dark:text-rose-400",
  slate: "text-ink-muted",
};

/**
 * A card whose whole plane is faintly tinted. The tint is the *only* thing
 * that differs from a neutral card — the border, radius and shadow are
 * identical, which is what keeps a wall of coloured cards from turning into
 * a wall of noise. Reserved for cards whose entire subject is one status
 * (a streak, a leader, an alert) rather than for decoration.
 */
export const TONE_CARD: Record<Tone, string> = {
  brand: "border-brand-500/25 bg-brand-50/50 dark:border-brand-500/25 dark:bg-brand-500/[0.07]",
  ember: "border-ember-500/25 bg-ember-50/50 dark:border-ember-500/25 dark:bg-ember-500/[0.07]",
  emerald: "border-emerald-500/25 bg-emerald-50/50 dark:border-emerald-500/25 dark:bg-emerald-500/[0.07]",
  amber: "border-amber-500/25 bg-amber-50/50 dark:border-amber-500/25 dark:bg-amber-500/[0.07]",
  orange: "border-orange-500/25 bg-orange-50/50 dark:border-orange-500/25 dark:bg-orange-500/[0.07]",
  rose: "border-rose-500/25 bg-rose-50/50 dark:border-rose-500/25 dark:bg-rose-500/[0.07]",
  slate: "border-line bg-surface",
};

/** Solid fill, for a single hero control in a row of neutrals. */
export const TONE_FILL: Record<Tone, string> = {
  brand: "bg-brand-600 hover:bg-brand-700",
  ember: "bg-ember-600 hover:bg-ember-700",
  emerald: "bg-emerald-600 hover:bg-emerald-700",
  amber: "bg-amber-500 hover:bg-amber-600",
  orange: "bg-orange-500 hover:bg-orange-600",
  rose: "bg-rose-600 hover:bg-rose-700",
  slate: "bg-slate-700 hover:bg-slate-800 dark:bg-slate-600 dark:hover:bg-slate-500",
};

/** Track + fill pair for progress bars and meters. */
export const TONE_TRACK: Record<Tone, string> = {
  brand: "bg-brand-500/15",
  ember: "bg-ember-500/15",
  emerald: "bg-emerald-500/15",
  amber: "bg-amber-500/15",
  orange: "bg-orange-500/15",
  rose: "bg-rose-500/15",
  slate: "bg-surface-raised",
};

export const TONE_BAR: Record<Tone, string> = {
  brand: "bg-brand-600",
  ember: "bg-ember-600",
  emerald: "bg-emerald-600",
  amber: "bg-amber-500",
  orange: "bg-orange-500",
  rose: "bg-rose-600",
  slate: "bg-ink-subtle",
};

/** Same hues as `TONE_BAR`, for SVG `stroke` (ring arcs, sparklines). */
export const TONE_STROKE: Record<Tone, string> = {
  brand: "stroke-brand-600",
  ember: "stroke-ember-600",
  emerald: "stroke-emerald-600",
  amber: "stroke-amber-500",
  orange: "stroke-orange-500",
  rose: "stroke-rose-600",
  slate: "stroke-ink-subtle",
};

/** Outline ring, for avatar halos and focusable accent edges. */
export const TONE_RING: Record<Tone, string> = {
  brand: "ring-brand-500/30",
  ember: "ring-ember-500/30",
  emerald: "ring-emerald-500/30",
  amber: "ring-amber-500/35",
  orange: "ring-orange-500/35",
  rose: "ring-rose-500/30",
  slate: "ring-line-strong",
};

/** Attendance is the clearest example of "colour means something". */
export const ATTENDANCE_TONE: Record<string, Tone> = {
  PRESENT: "emerald",
  LATE: "amber",
  ABSENT: "rose",
  EXCUSED: "slate",
};

export const ATTENDANCE_LABEL: Record<string, string> = {
  PRESENT: "Keldi",
  LATE: "Kechikdi",
  ABSENT: "Kelmadi",
  EXCUSED: "Sababli",
};
