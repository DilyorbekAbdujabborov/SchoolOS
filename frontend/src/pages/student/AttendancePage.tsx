import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Field, Input } from "../../components/form";
import { PageHeader } from "../../components/PageHeader";
import { StatCard } from "../../components/StatCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { Table, Tbody, Td, Th, Thead, Tr } from "../../components/table";
import { api } from "../../lib/api";
import { SCHOOL_WEEKDAYS } from "../../lib/schoolTime";
import type { AttendanceRecord, AttendanceStatus, Paginated, StudentDashboard } from "../../types";

/** Walks `?page=` until every page is collected — a plain `.get()` only
 * returns the first `PAGE_SIZE` (20) records, which can silently drop the
 * week's earlier days once a student has more than 20 lesson-attendance
 * rows in the range (the API orders newest-first). Capped at 10 pages as a
 * sanity bound; a single school week never comes close. */
async function fetchAllPages<T>(url: string, params: Record<string, unknown>): Promise<T[]> {
  const results: T[] = [];
  let page = 1;
  let hasNext = true;
  while (hasNext && page <= 10) {
    const { data } = await api.get<Paginated<T>>(url, { params: { ...params, page } });
    results.push(...data.results);
    hasNext = Boolean(data.next);
    page += 1;
  }
  return results;
}

const STATUS_LABEL: Record<string, string> = {
  PRESENT: "Keldi",
  LATE: "Kechikdi",
  ABSENT: "Kelmadi",
  EXCUSED: "Sababli",
};

const DAY_TONE: Record<AttendanceStatus | "NONE", string> = {
  PRESENT: "bg-emerald-500 text-white",
  LATE: "bg-amber-500 text-white",
  ABSENT: "bg-red-500 text-white",
  EXCUSED: "bg-slate-400 text-white",
  NONE: "bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-600",
};

// Worst-first — a day with even one ABSENT record shows as absent overall.
const SEVERITY: AttendanceStatus[] = ["ABSENT", "LATE", "EXCUSED", "PRESENT"];

function currentWeekRange(): { monday: string; saturday: string } {
  const now = new Date();
  const jsDay = now.getDay(); // 0=Sunday
  const diffToMonday = jsDay === 0 ? -6 : 1 - jsDay;
  const monday = new Date(now);
  monday.setDate(now.getDate() + diffToMonday);
  const saturday = new Date(monday);
  saturday.setDate(monday.getDate() + 5);
  const iso = (d: Date) => d.toISOString().slice(0, 10);
  return { monday: iso(monday), saturday: iso(saturday) };
}

function WeeklyStrip() {
  const { monday, saturday } = currentWeekRange();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["attendance", "week", monday],
    queryFn: () =>
      fetchAllPages<AttendanceRecord>("/attendance/", { date_from: monday, date_to: saturday }),
  });

  const byDate = new Map<string, AttendanceRecord[]>();
  for (const record of data ?? []) {
    const list = byDate.get(record.lesson_date) ?? [];
    list.push(record);
    byDate.set(record.lesson_date, list);
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <p className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">Bu hafta</p>
      {isLoading && <LoadingState label="Yuklanmoqda..." />}
      {isError && <ErrorState message="Haftalik davomat yuklanmadi." />}
      {data && (
        <div className="grid grid-cols-6 gap-2">
          {SCHOOL_WEEKDAYS.map((day, index) => {
            const date = new Date(monday);
            date.setDate(date.getDate() + index);
            const iso = date.toISOString().slice(0, 10);
            const records = byDate.get(iso) ?? [];
            const worst = SEVERITY.find((s) => records.some((r) => r.status === s));
            const tone = worst ? DAY_TONE[worst] : DAY_TONE.NONE;
            return (
              <div key={day.value} className="flex flex-col items-center gap-1.5">
                <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">{day.short}</span>
                <span className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${tone}`}>
                  {date.getDate()}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export function StudentAttendancePage() {
  const [date, setDate] = useState("");

  const summaryQuery = useQuery({
    queryKey: ["dashboard", "student"],
    queryFn: async () => (await api.get<StudentDashboard>("/dashboard/student/")).data,
  });

  const historyQuery = useQuery({
    queryKey: ["attendance", "history", date],
    queryFn: async () =>
      (
        await api.get<Paginated<AttendanceRecord>>("/attendance/", {
          params: { date: date || undefined },
        })
      ).data,
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Mening davomatim" />

      {summaryQuery.isLoading && <LoadingState />}
      {summaryQuery.data && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Keldi" value={summaryQuery.data.attendance_summary.present} />
          <StatCard label="Kechikdi" value={summaryQuery.data.attendance_summary.late} />
          <StatCard label="Kelmadi" value={summaryQuery.data.attendance_summary.absent} />
          <StatCard label="Sababli" value={summaryQuery.data.attendance_summary.excused} />
        </div>
      )}

      <WeeklyStrip />

      <Field label="Sana">
        <Input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="max-w-[180px]"
        />
      </Field>

      {historyQuery.isLoading && <LoadingState />}
      {historyQuery.isError && <ErrorState />}
      {historyQuery.data && historyQuery.data.results.length === 0 && (
        <EmptyState title="Bu filtrga mos davomat yozuvi yo'q" />
      )}

      {historyQuery.data && historyQuery.data.results.length > 0 && (
        <Table>
          <Thead>
            <Tr>
              <Th>Sana</Th>
              <Th>Fan</Th>
              <Th>Holat</Th>
            </Tr>
          </Thead>
          <Tbody>
            {historyQuery.data.results.map((record) => (
              <Tr key={record.id}>
                <Td className="text-slate-700 dark:text-slate-200">{record.lesson_date}</Td>
                <Td className="text-slate-700 dark:text-slate-200">{record.subject_name}</Td>
                <Td className="text-slate-700 dark:text-slate-200">
                  {STATUS_LABEL[record.status] ?? record.status}
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </div>
  );
}
