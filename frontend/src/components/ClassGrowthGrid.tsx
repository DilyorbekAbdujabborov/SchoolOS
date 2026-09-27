import { useState } from "react";
import { TrendingDown, TrendingUp } from "lucide-react";

import { distinctGrades, gradeNumber } from "../lib/classGrade";
import { TONE_DOT, type Tone } from "../lib/tones";
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

/**
 * Class comparison, one ring per class.
 *
 * The ring tone is derived from the *sign of the growth*, not from a rotating
 * palette — so a wall of these reads instantly as "which classes are moving
 * and which are stalled" without any legend. A negative ring is rendered as
 * its absolute magnitude (a ring can't sweep backwards) and called out with a
 * red delta, so no class silently looks like a winner.
 */
export function ClassGrowthGrid({ series }: { series: ClassGrowthSeries[] }) {
  const [filter, setFilter] = useState<number | "all">("all");

  const grades = distinctGrades(series.map((s) => s.class_name));
  const filtered = filter === "all" ? series : series.filter((s) => gradeNumber(s.class_name) === filter);

  if (series.length === 0) {
    return (
      <EmptyState
        title="Hali XP ma'lumoti yo'q"
        description="O'quvchilar test va topshiriq bajarganachagacha o'sish grafigi bo'sh qoladi."
      />
    );
  }

  return (
    <div className="space-y-4">
      <FilterPills
        value={filter}
        onChange={setFilter}
        options={[
          { value: "all" as const, label: "Barcha sinflar", count: series.length },
          ...grades.map((grade) => ({
            value: grade,
            label: `${grade}-sinflar`,
            count: series.filter((s) => gradeNumber(s.class_name) === grade).length,
          })),
        ]}
      />

      {filtered.length === 0 ? (
        <EmptyState title="Bu filtrga mos sinf topilmadi" />
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {filtered.map((s) => {
            const percent = growthPercent(s);
            const falling = percent < 0;
            const flat = percent === 0;
            const tone: Tone = falling ? "rose" : flat ? "slate" : percent >= 25 ? "emerald" : "brand";
            const last = s.points[s.points.length - 1]?.total_xp ?? 0;

            return (
              <div
                key={s.class_id}
                className="card hover-card flex flex-col items-center gap-2 p-4"
              >
                <CircularProgress
                  value={Math.abs(percent)}
                  tone={tone}
                  size={84}
                  strokeWidth={8}
                  caption={s.class_name}
                >
                  <span
                    className={`tabular text-lg font-bold ${
                      falling ? "text-rose-600 dark:text-rose-400" : "text-ink"
                    }`}
                  >
                    {percent > 0 ? "+" : ""}
                    {percent}%
                  </span>
                </CircularProgress>
                <p className="flex items-center gap-1 text-xs font-medium text-ink-muted">
                  {falling ? (
                    <TrendingDown size={12} className="text-rose-500" />
                  ) : flat ? (
                    <span className={`h-1.5 w-1.5 rounded-full ${TONE_DOT.slate}`} />
                  ) : (
                    <TrendingUp size={12} className="text-emerald-500" />
                  )}
                  {falling ? "pasayish" : flat ? "o'zgarish yo'q" : "o'sish"}
                </p>
                <p className="tabular text-[11px] text-ink-subtle">{last} XP jami</p>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
