import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { useTheme } from "../../lib/theme";
import type { ClassGrowthSeries } from "../../types";

const LINE_COLORS = ["#4f46e5", "#10b981", "#f59e0b", "#f43f5e", "#06b6d4", "#8b5cf6", "#ea580c", "#0d9488"];

function formatDateLabel(iso: string) {
  return new Date(iso).toLocaleDateString("uz-UZ", { day: "2-digit", month: "2-digit" });
}

/** Reshapes N per-class series into recharts' expected "one row per date,
 * one column per class" table. */
function buildRows(series: ClassGrowthSeries[]) {
  if (series.length === 0) return [];
  return series[0].points.map((point, index) => {
    const row: Record<string, string | number> = { date: formatDateLabel(point.date) };
    for (const classSeries of series) {
      row[classSeries.class_name] = classSeries.points[index]?.total_xp ?? 0;
    }
    return row;
  });
}

export function ClassGrowthChart({ series }: { series: ClassGrowthSeries[] }) {
  const { theme } = useTheme();
  const gridColor = theme === "dark" ? "#1e293b" : "#e2e8f0";
  const tickColor = theme === "dark" ? "#64748b" : "#94a3b8";

  if (series.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-slate-400 dark:text-slate-500">Hali sinf ma'lumoti yo'q</p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={buildRows(series)} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={gridColor} />
        <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: tickColor }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: tickColor }} width={40} />
        <Tooltip
          contentStyle={{
            borderRadius: 8,
            fontSize: 12,
            border: `1px solid ${gridColor}`,
            backgroundColor: theme === "dark" ? "#0f172a" : "#ffffff",
            color: theme === "dark" ? "#e2e8f0" : "#0f172a",
          }}
        />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {series.map((classSeries, index) => (
          <Line
            key={classSeries.class_id}
            type="monotone"
            dataKey={classSeries.class_name}
            stroke={LINE_COLORS[index % LINE_COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
