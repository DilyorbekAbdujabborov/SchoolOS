import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { AXIS_PROPS, useChartTheme } from "../../lib/chartTheme";
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
  const theme = useChartTheme();
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;
  return (
    <div className={theme.tooltip.content}>
      <p className={theme.tooltip.label}>{point.label}</p>
      <p className="font-semibold text-emerald-600 dark:text-emerald-400">Keldi: {point.present}</p>
      <p className="font-semibold text-amber-600 dark:text-amber-400">Kechikdi: {point.late}</p>
      <p className="font-semibold text-rose-600 dark:text-rose-400">Kelmadi: {point.absent}</p>
      <p className={theme.tooltip.value}>Sababli: {point.excused}</p>
    </div>
  );
}

/**
 * Daily attendance. The bars encode the thing you actually scan for — how many
 * were present — in brand blue; the absence/lateness breakdown lives in the
 * tooltip and in the red/amber lines beside the chart, so the plot itself
 * stays monochrome and calm.
 */
export function AttendanceDailyChart({ data }: { data: AttendanceDailyCount[] }) {
  const theme = useChartTheme();
  const rows: Row[] = data.map((d) => ({ ...d, label: shortDateLabel(d.date) }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={rows} margin={{ top: 8, right: 8, left: -14, bottom: 0 }} barCategoryGap="18%">
        <CartesianGrid vertical={false} stroke={theme.grid} />
        <XAxis
          dataKey="label"
          {...AXIS_PROPS}
          tick={{ ...AXIS_PROPS.tick, fill: theme.axis }}
          interval="preserveStartEnd"
          minTickGap={18}
        />
        <YAxis {...AXIS_PROPS} tick={{ ...AXIS_PROPS.tick, fill: theme.axis }} width={40} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: theme.cursor }} />
        <Bar
          dataKey="present"
          fill={theme.tone("brand")}
          radius={[6, 6, 0, 0]}
          maxBarSize={34}
          className="chart-enter"
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
