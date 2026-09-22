import { useState } from "react";

import { distinctGrades, gradeNumber } from "../lib/classGrade";
import type { ClassGrowthSeries } from "../types";
import { CircularProgress } from "./CircularProgress";
import { FilterPills } from "./FilterPills";
import { EmptyState } from "./states";

/** Percent change in a class's total XP from the start to the end of the
 * chart's date range — the same underlying data the old line chart plotted,
 * just read as a single number per class instead of a full time series. */
function growthPercent(series: ClassGrowthSeries): number {
  const points = series.points;
  if (points.length < 2) return 0;
  const start = points[0].total_xp;
  const end = points[points.length - 1].total_xp;
  if (start <= 0) return end > 0 ? 100 : 0;
  return Math.round(((end - start) / start) * 100);
}

export function ClassGrowthGrid({ series }: { series: ClassGrowthSeries[] }) {
  const [filter, setFilter] = useState<number | "all">("all");

  const grades = distinctGrades(series.map((s) => s.class_name));
  const filtered = filter === "all" ? series : series.filter((s) => gradeNumber(s.class_name) === filter);

  if (series.length === 0) {
    return <EmptyState title="Hali XP ma'lumoti yo'q" />;
  }

  return (
    <div className="space-y-4">
      <FilterPills
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all" as const, label: "Barcha sinflar" },
          ...grades.map((grade) => ({ value: grade, label: `${grade}-sinflar` })),
        ]}
      />

      {filtered.length === 0 ? (
        <EmptyState title="Bu filtrga mos sinf topilmadi" />
      ) : (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {filtered.map((s) => {
            const percent = growthPercent(s);
            return (
              <div
                key={s.class_id}
                className="hover-card flex flex-col items-center gap-1 rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
              >
                <CircularProgress value={Math.max(0, Math.min(100, percent))} size={88} strokeWidth={8} label={s.class_name} />
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  {percent >= 0 ? "+" : ""}
                  {percent}% o'sish
                </p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
