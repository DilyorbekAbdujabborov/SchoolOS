import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

import { TONE_BAR, TONE_CARD, TONE_CHIP, TONE_TRACK, type Tone } from "../lib/tones";

export type StatDelta = {
  value: number;
  /** Words after the number, e.g. "o'tgan hafta". */
  label?: string;
};

interface StatCardProps {
  label: string;
  value: string | number;
  /** Secondary line under the value — context, not decoration. */
  hint?: string;
  /** Signed change vs. a previous period. Rendered as a green/red delta. */
  delta?: StatDelta;
  /** A 0–100 meter drawn under the value, for rates and ratios. */
  meter?: number;
  /** When set, the whole card becomes a link — for stats that lead somewhere. */
  to?: string;
  /** When set instead of `to`, the card becomes a button — for stats that
   * drill down in place (e.g. expanding a list) rather than navigating. */
  onClick?: () => void;
  icon?: LucideIcon;
  tone?: Tone;
  /** The one hero stat per view: bigger type, tinted plane, a little more air. */
  emphasis?: boolean;
}

/**
 * A single number.
 *
 * Tiles are neutral by default and take their colour from the icon chip and
 * the meter, not from the card surface — a grid of stats should read as one
 * clean matrix, not as a grid of coloured boxes. Pass `tone` to tint the
 * whole card, but only for the stat a view is actually about.
 */
export function StatCard({
  label,
  value,
  hint,
  delta,
  meter,
  to,
  onClick,
  icon: Icon,
  tone = "slate",
  emphasis = false,
}: StatCardProps) {
  const surface = emphasis
    ? `${TONE_CARD[tone]} shadow-raise`
    : "card hover-card";
  const className = `${surface} ${emphasis ? "p-6" : "p-4 sm:p-5"} text-left`;

  const content = (
    <>
      <div className="flex items-start justify-between gap-2">
        <p className="text-[13px] font-medium text-ink-muted">{label}</p>
        {Icon && (
          <span
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${TONE_CHIP[tone]}`}
          >
            <Icon size={16} />
          </span>
        )}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <p className={`stat-value ${emphasis ? "text-[34px] leading-none" : ""}`}>{value}</p>
        {delta && <DeltaBadge delta={delta} />}
      </div>
      {meter !== undefined && (
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface-sunken">
          <div
            className={`h-full rounded-full ${TONE_BAR[tone]} transition-[width] duration-700 ease-out`}
            style={{ width: `${Math.min(100, Math.max(0, meter))}%` }}
          />
        </div>
      )}
      {hint && <p className="mt-1.5 text-xs text-ink-subtle">{hint}</p>}
    </>
  );

  if (to) {
    return (
      <Link to={to} className={`${className} block`}>
        {content}
      </Link>
    );
  }

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={`${className} block w-full`}>
        {content}
      </button>
    );
  }

  return <div className={className}>{content}</div>;
}

function DeltaBadge({ delta }: { delta: StatDelta }) {
  const up = delta.value > 0;
  const flat = delta.value === 0;
  return (
    <span
      className={`inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-semibold tabular ${
        flat
          ? "bg-surface-raised text-ink-subtle"
          : up
            ? "bg-emerald-500/12 text-emerald-700 dark:text-emerald-400"
            : "bg-rose-500/12 text-rose-700 dark:text-rose-400"
      }`}
    >
      {!flat && (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d={up ? "M12 19V5m0 0-6 6m6-6 6 6" : "M12 5v14m0 0 6-6m-6 6-6-6"}
            stroke="currentColor"
            strokeWidth="2.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      )}
      {up ? "+" : ""}
      {delta.value}
      {delta.label ? `%` : ""}
    </span>
  );
}

/**
 * A compact labelled meter — the dense alternative to `StatCard` for panels
 * that list several rates (per-class attendance, per-subject averages).
 */
export function MeterRow({
  label,
  value,
  caption,
  tone = "brand",
}: {
  label: React.ReactNode;
  /** 0–100. */
  value: number;
  caption?: React.ReactNode;
  tone?: Tone;
}) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-3">
        <span className="truncate text-sm font-medium text-ink">{label}</span>
        <span className="tabular shrink-0 text-sm font-semibold text-ink">{Math.round(clamped)}%</span>
      </div>
      <div className={`h-1.5 w-full overflow-hidden rounded-full ${TONE_TRACK[tone]}`}>
        <div
          className={`h-full rounded-full ${TONE_BAR[tone]} transition-[width] duration-700 ease-out`}
          style={{ width: `${clamped}%` }}
        />
      </div>
      {caption && <p className="mt-1 text-xs text-ink-subtle">{caption}</p>}
    </div>
  );
}
