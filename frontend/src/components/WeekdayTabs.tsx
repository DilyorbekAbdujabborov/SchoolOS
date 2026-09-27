import { SCHOOL_WEEKDAYS } from "../lib/schoolTime";
import { TONE_FILL } from "../lib/tones";

/** The Dushanba–Shanba day selector shared by the teacher and student weekly
 * schedule views — deliberately not a full calendar, per the design brief.
 * Horizontally scrollable so it never breaks the layout on narrow screens.
 *
 * The selected day is the one solid fill in the row; the rest are neutral
 * surfaces. That keeps a 6-button control from reading as six blue boxes. */
export function WeekdayTabs({ value, onChange }: { value: number; onChange: (day: number) => void }) {
  return (
    <div
      role="tablist"
      className="-mx-1 flex gap-2 overflow-x-auto px-1 py-0.5"
      style={{ scrollbarWidth: "none" }}
    >
      {SCHOOL_WEEKDAYS.map((day) => {
        const active = day.value === value;
        return (
          <button
            key={day.value}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(day.value)}
            className={`shrink-0 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-all duration-150 ${
              active
                ? `border-transparent text-white shadow-raise ${TONE_FILL.brand}`
                : "border-line bg-surface text-ink-muted hover:border-line-strong hover:bg-surface-raised hover:text-ink"
            }`}
          >
            <span className="hidden sm:inline">{day.label}</span>
            <span className="sm:hidden">{day.short}</span>
          </button>
        );
      })}
    </div>
  );
}
