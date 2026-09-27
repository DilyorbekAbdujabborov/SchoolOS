import type { ReactNode } from "react";

import { TONE_FILL, type Tone } from "../lib/tones";

/**
 * A horizontally-scrollable row of segmented filter pills — shared by every
 * "pick one of a few categories" filter in the app (grade level, class, date
 * range) so they all look and behave identically. The active pill is the only
 * solid fill on the row, so the current filter is obvious without a border
 * fight.
 */
export function FilterPills<T extends string | number>({
  options,
  value,
  onChange,
  tone = "brand",
}: {
  options: { value: T; label: ReactNode; count?: number }[];
  value: T;
  onChange: (value: T) => void;
  tone?: Tone;
}) {
  return (
    <div
      role="tablist"
      className="-mx-1 flex gap-2 overflow-x-auto px-1 py-0.5"
      style={{ scrollbarWidth: "none" }}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={String(option.value)}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(option.value)}
            className={`shrink-0 rounded-full border px-3.5 py-1.5 text-sm font-medium text-white transition-colors duration-150 ${
              active
                ? `border-transparent shadow-sm ${TONE_FILL[tone]}`
                : "border-line bg-surface text-ink-muted hover:border-line-strong hover:text-ink"
            }`}
          >
            {option.label}
            {option.count !== undefined && (
              <span className="tabular ml-1.5 text-xs opacity-70">{option.count}</span>
            )}
          </button>
        );
      })}
    </div>
  );
}
