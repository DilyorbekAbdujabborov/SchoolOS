import { SCHOOL_WEEKDAYS } from "../lib/schoolTime";

/** The Dushanba–Shanba day selector shared by the teacher and student weekly
 * schedule views — deliberately not a full calendar, per the design brief.
 * Horizontally scrollable so it never breaks the layout on narrow screens.
 */
export function WeekdayTabs({ value, onChange }: { value: number; onChange: (day: number) => void }) {
  return (
    <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
      {SCHOOL_WEEKDAYS.map((day) => {
        const active = day.value === value;
        return (
          <button
            key={day.value}
            type="button"
            onClick={() => onChange(day.value)}
            className={`shrink-0 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-colors ${
              active
                ? "border-brand-500 bg-brand-600 text-white shadow-[0_0_0_1px_rgba(37,99,235,0.15),0_8px_20px_-8px_rgba(37,99,235,0.5)] dark:border-brand-400"
                : "hover-card border-slate-200 bg-white text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300"
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
