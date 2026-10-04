import { useTheme } from "./theme";

/**
 * Chart design tokens.
 *
 * A dashboard's charts are where "everything is blue" usually leaks out, so
 * the rules are explicit here rather than left to each page:
 *
 *   • A chart is monochrome by default. One series → one hue, chosen by what
 *     the metric *means*, not by what looks nice.
 *   • A second series only appears when the two are genuinely different
 *     kinds of thing (present vs. absent, this class vs. last class) and then
 *     takes a different tone — never a random one.
 *   • Grid, ticks, labels and tooltips all come from the same neutral token
 *     set as the rest of the UI, so charts sit *inside* the design system
 *     instead of on top of it.
 */

/** A named role in a chart, resolved to a real colour per theme. */
export type ChartTone = "brand" | "violet" | "emerald" | "amber" | "rose" | "slate";

const LIGHT: Record<ChartTone, string> = {
  brand: "#0a8f80",
  violet: "#7c3aed",
  emerald: "#059669",
  amber: "#d97706",
  rose: "#e11d48",
  slate: "#94a3b8",
};

const DARK: Record<ChartTone, string> = {
  brand: "#2fd3bc",
  violet: "#a78bfa",
  emerald: "#34d399",
  amber: "#fbbf24",
  rose: "#fb7185",
  slate: "#64748b",
};

const SERIES_LIGHT = ["#0a8f80", "#7c3aed", "#059669", "#d97706", "#e11d48", "#0891b2", "#94a3b8"];
const SERIES_DARK = ["#2fd3bc", "#a78bfa", "#34d399", "#fbbf24", "#fb7185", "#22d3ee", "#64748b"];

export interface ChartTheme {
  /** Fill for a single-series chart. */
  series: string[];
  tone: (name: ChartTone) => string;
  grid: string;
  axis: string;
  /** Cursor / hover band behind a hovered bar or point. */
  cursor: string;
  /** Recharts tooltip body + item styling, shared by every chart. */
  tooltip: {
    content: string;
    label: string;
    value: string;
    separator: string;
  };
}

export function useChartTheme(): ChartTheme {
  const { theme } = useTheme();
  const dark = theme === "dark";

  return {
    series: dark ? SERIES_DARK : SERIES_LIGHT,
    tone: (name) => (dark ? DARK[name] : LIGHT[name]),
    grid: dark ? "rgb(38 44 57)" : "rgb(225 228 234)",
    axis: dark ? "rgb(108 116 132)" : "rgb(138 146 165)",
    cursor: dark ? "rgb(255 255 255 / 0.04)" : "rgb(16 24 40 / 0.035)",
    tooltip: {
      content:
        "rounded-xl border border-line bg-surface px-3 py-2 text-xs shadow-pop dark:border-line-strong",
      label: "mb-1 font-semibold text-ink",
      value: "text-ink-muted",
      separator: "text-ink-subtle",
    },
  };
}

/** Shared props for a Recharts axis: no axis line, no ticks, muted labels. */
export const AXIS_PROPS = {
  axisLine: false,
  tickLine: false,
  tick: { fontSize: 11 },
} as const;
