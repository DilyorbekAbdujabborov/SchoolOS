import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { useTheme } from "../../lib/theme";
import type { AttendanceDailyCount } from "../../types";

// "kun.oy" (e.g. "21.09") rather than a 3-letter month name — Uzbek month
// names collide when truncated to 3 letters (Iyun/Iyul both become "Iyu"),
// which made adjacent days in a 30-day range indistinguishable on the axis.
function shortDateLabel(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getDate()).padStart(2, "0")}.${String(d.getMonth() + 1).padStart(2, "0")}`;
}

interface Row extends AttendanceDailyCount {
  label: string;
}

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: Row }[] }) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-xs shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <p className="mb-1.5 font-semibold text-slate-800 dark:text-slate-100">{point.label}</p>
      <p className="text-emerald-600 dark:text-emerald-400">Keldi: {point.present}</p>
      <p className="text-amber-600 dark:text-amber-400">Kechikdi: {point.late}</p>
      <p className="text-red-600 dark:text-red-400">Kelmadi: {point.absent}</p>
      <p className="text-slate-500 dark:text-slate-400">Sababli: {point.excused}</p>
    </div>
  );
}

export function AttendanceDailyChart({ data }: { data: AttendanceDailyCount[] }) {
  const { theme } = useTheme();
  const gridColor = theme === "dark" ? "#1c212c" : "#e1e4ea";
  const tickColor = theme === "dark" ? "#6b7280" : "#98a0b3";
  const barColor = theme === "dark" ? "#3b82f6" : "#2563eb";
  const cursorColor = theme === "dark" ? "rgba(59,130,246,0.10)" : "rgba(37,99,235,0.06)";

  const rows: Row[] = data.map((d) => ({ ...d, label: shortDateLabel(d.date) }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={gridColor} />
        <XAxis
          dataKey="label"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: tickColor }}
          interval="preserveStartEnd"
          minTickGap={16}
        />
        <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: tickColor }} width={36} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: cursorColor }} />
        <Bar dataKey="present" fill={barColor} radius={[6, 6, 0, 0]} maxBarSize={36} />
      </BarChart>
    </ResponsiveContainer>
  );
}
