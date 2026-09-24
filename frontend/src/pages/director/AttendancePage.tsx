import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BarChart3, CheckCircle2, Phone, X } from "lucide-react";
import { lazy, Suspense, useEffect, useState } from "react";

import { Badge } from "../../components/Badge";
import { Field, Input, Select } from "../../components/form";
import { FilterPills } from "../../components/FilterPills";
import { PageHeader } from "../../components/PageHeader";
import { StatCard } from "../../components/StatCard";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { Table, Tbody, Td, Th, Thead, Tr } from "../../components/table";
import { api } from "../../lib/api";
import { distinctGrades } from "../../lib/classGrade";
import type {
  AttendanceDailyCount,
  AttendanceRecord,
  AttendanceRosterStudent,
  AttendanceStatus,
  ClassAttendanceSummary,
  DirectorDashboard,
  LessonAttendanceStatus,
  Paginated,
  SchoolClass,
} from "../../types";

const AttendanceDailyChart = lazy(() =>
  import("../../components/charts/AttendanceDailyChart").then((m) => ({ default: m.AttendanceDailyChart })),
);

const DAY_RANGE_OPTIONS = [
  { value: 7, label: "Oxirgi 7 kun" },
  { value: 14, label: "Oxirgi 14 kun" },
  { value: 30, label: "Oxirgi 30 kun" },
];

const STATUS_LABEL: Record<string, string> = {
  PRESENT: "Keldi",
  LATE: "Kechikdi",
  ABSENT: "Kelmadi",
  EXCUSED: "Sababli",
};

const STATUS_TONE: Record<AttendanceStatus, "emerald" | "amber" | "red" | "slate"> = {
  PRESENT: "emerald",
  LATE: "amber",
  ABSENT: "red",
  EXCUSED: "slate",
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

/** Re-renders every 30 seconds so "davomat olinmagan" flips off the moment a
 * lesson is marked, without a manual refresh. */
function useNow() {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 30_000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function unmarkedLessonStatus(lesson: LessonAttendanceStatus, now: number) {
  const end = new Date(`${lesson.date}T${lesson.end_time}`).getTime();
  const start = new Date(`${lesson.date}T${lesson.start_time}`).getTime();
  if (now < start) return null; // hasn't happened yet — nothing missing
  if (now < end) return { label: "Kutilmoqda", tone: "amber" as const };
  return { label: "Davomat olinmagan", tone: "red" as const };
}

type RosterFilter = "LATE" | "ABSENT" | null;

function StudentRosterList({ students }: { students: AttendanceRosterStudent[] }) {
  if (students.length === 0) {
    return <p className="px-5 py-4 text-sm text-slate-400 dark:text-slate-500">Ro'yxat bo'sh.</p>;
  }
  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-800">
      {students.map((student) => (
        <div key={student.id} className="flex items-center justify-between gap-3 px-5 py-3">
          <span className="font-medium text-slate-800 dark:text-slate-100">{student.full_name}</span>
          {student.parent_phone_number ? (
            <a
              href={`tel:${student.parent_phone_number}`}
              className="flex items-center gap-1.5 text-sm text-brand-600 hover:underline dark:text-brand-400"
            >
              <Phone className="h-3.5 w-3.5" /> {student.parent_phone_number}
            </a>
          ) : (
            <span className="text-sm text-slate-400 dark:text-slate-500">
              Ota-ona raqami kiritilmagan
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

export function AttendancePage() {
  const [selectedClass, setSelectedClass] = useState("");
  const [date, setDate] = useState(todayIso());
  const [rosterFilter, setRosterFilter] = useState<RosterFilter>(null);
  const [dayRange, setDayRange] = useState(14);
  const [gradeFilter, setGradeFilter] = useState<number | "all">("all");
  const now = useNow();

  const { data: classes } = useQuery({
    queryKey: ["classes"],
    queryFn: async () => (await api.get<Paginated<SchoolClass>>("/classes/")).data,
  });

  const { data: dashboard } = useQuery({
    queryKey: ["dashboard", "director"],
    queryFn: async () => (await api.get<DirectorDashboard>("/dashboard/director/")).data,
  });

  const dailyQuery = useQuery({
    queryKey: ["attendance", "daily-summary", dayRange, gradeFilter],
    queryFn: async () =>
      (
        await api.get<AttendanceDailyCount[]>("/attendance/daily-summary/", {
          params: { days: dayRange, grade: gradeFilter === "all" ? undefined : gradeFilter },
        })
      ).data,
  });

  const grades = distinctGrades((classes?.results ?? []).map((c) => c.name));

  const summaryQuery = useQuery({
    queryKey: ["attendance", "class-summary", selectedClass, date],
    enabled: Boolean(selectedClass),
    queryFn: async () =>
      (
        await api.get<ClassAttendanceSummary>("/attendance/class-summary/", {
          params: { school_class: selectedClass, date },
        })
      ).data,
  });

  const historyQuery = useQuery({
    queryKey: ["attendance", "history", selectedClass, date],
    queryFn: async () =>
      (
        await api.get<Paginated<AttendanceRecord>>("/attendance/", {
          params: { school_class: selectedClass || undefined, date: date || undefined },
        })
      ).data,
  });

  const unmarkedQuery = useQuery({
    queryKey: ["attendance", "lesson-status", selectedClass, date],
    queryFn: async () =>
      (
        await api.get<LessonAttendanceStatus[]>("/attendance/lesson-summary/", {
          params: { date: date || undefined, school_class: selectedClass || undefined },
        })
      ).data,
  });

  // Lessons that already happened (or are running) but never got attendance.
  const unmarkedRows =
    (unmarkedQuery.data ?? [])
      .map((lesson) => ({ lesson, status: unmarkedLessonStatus(lesson, now) }))
      .filter((row): row is { lesson: LessonAttendanceStatus; status: { label: string; tone: "amber" | "red" } } => row.status !== null);

  return (
    <div className="space-y-6">
      <PageHeader title="Davomat" />

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">Bugungi davomat</h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
          <StatCard label="Jami o'quvchilar" value={dashboard?.total_students ?? "—"} />
          <StatCard label="Keldi" value={dashboard?.today_attendance.present ?? "—"} tone="emerald" />
          <StatCard label="Kechikdi" value={dashboard?.today_attendance.late ?? "—"} tone="amber" />
          <StatCard label="Kelmadi" value={dashboard?.today_attendance.absent ?? "—"} tone="rose" />
          <StatCard label="Sababli" value={dashboard?.today_attendance.excused ?? "—"} tone="brand" />
        </div>
      </section>

      <section>
        <div className="mb-3 flex items-center gap-2">
          <BarChart3 size={16} className="text-brand-600 dark:text-brand-400" />
          <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
            Kunlik davomat — maktab bo'yicha necha o'quvchi darsga keldi
          </h2>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <FilterPills value={dayRange} onChange={setDayRange} options={DAY_RANGE_OPTIONS} />
            <FilterPills
              value={gradeFilter}
              onChange={setGradeFilter}
              options={[
                { value: "all" as const, label: "Barcha maktab" },
                ...grades.map((grade) => ({ value: grade, label: `${grade}-sinflar` })),
              ]}
            />
          </div>
          {dailyQuery.isLoading && <LoadingState />}
          {dailyQuery.isError && <ErrorState />}
          {dailyQuery.data && (
            <Suspense fallback={<LoadingState label="Yuklanmoqda..." />}>
              <AttendanceDailyChart data={dailyQuery.data} />
            </Suspense>
          )}
        </div>
      </section>

      <div className="flex flex-wrap gap-3">
        <Field label="Sinf">
          <Select
            value={selectedClass}
            onChange={(e) => {
              setSelectedClass(e.target.value);
              setRosterFilter(null);
            }}
            className="min-w-[160px]"
          >
            <option value="">Barcha sinflar</option>
            {classes?.results.map((cls) => (
              <option key={cls.id} value={cls.id}>
                {cls.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Sana">
          <Input
            type="date"
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              setRosterFilter(null);
            }}
            className="min-w-[160px]"
          />
        </Field>
      </div>

      {selectedClass && summaryQuery.isLoading && <LoadingState />}
      {selectedClass && summaryQuery.isError && <ErrorState />}
      {selectedClass && summaryQuery.data && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-5">
            <StatCard label="Jami o'quvchi" value={summaryQuery.data.total_students} />
            <StatCard label="Keldi" value={summaryQuery.data.present} />
            <StatCard
              label="Kechikdi"
              value={summaryQuery.data.late}
              onClick={() => setRosterFilter(rosterFilter === "LATE" ? null : "LATE")}
            />
            <StatCard
              label="Kelmadi"
              value={summaryQuery.data.absent}
              onClick={() => setRosterFilter(rosterFilter === "ABSENT" ? null : "ABSENT")}
            />
            <StatCard label="Sababli" value={summaryQuery.data.excused} />
          </div>

          {rosterFilter && (
            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3 dark:border-slate-800">
                <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                  {rosterFilter === "LATE" ? "Kechikkanlar" : "Kelmaganlar"}
                </h3>
                <button
                  onClick={() => setRosterFilter(null)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <StudentRosterList
                students={
                  rosterFilter === "LATE"
                    ? summaryQuery.data.late_students
                    : summaryQuery.data.absent_students
                }
              />
            </div>
          )}
        </>
      )}

      <div>
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
            <AlertTriangle size={16} className="text-red-500" />
            Davomat olinmagan darslar
          </h2>
          {unmarkedQuery.data && (
            <span className="text-xs text-slate-400 dark:text-slate-500">
              {unmarkedRows.length} ta dars
            </span>
          )}
        </div>
        {unmarkedQuery.isLoading && <LoadingState />}
        {unmarkedQuery.isError && <ErrorState />}
        {unmarkedQuery.data && (
          <Table>
            <Thead>
              <Tr>
                <Th>Vaqti</Th>
                <Th>Sinf</Th>
                <Th>Fan</Th>
                <Th>O'qituvchi</Th>
                <Th>Holat</Th>
              </Tr>
            </Thead>
            <Tbody>
              {unmarkedRows.map(({ lesson, status }) => (
                  <Tr key={lesson.id}>
                    <Td className="text-slate-500 dark:text-slate-400">
                      {lesson.start_time.slice(0, 5)}–{lesson.end_time.slice(0, 5)}
                    </Td>
                    <Td className="text-slate-700 dark:text-slate-200">{lesson.school_class_name}</Td>
                    <Td className="text-slate-700 dark:text-slate-200">{lesson.subject_name}</Td>
                    <Td className="text-slate-700 dark:text-slate-200">{lesson.teacher_name}</Td>
                    <Td>
                      <Badge tone={status.tone}>{status.label}</Badge>
                    </Td>
                  </Tr>
                ))}
            </Tbody>
          </Table>
        )}
        {unmarkedQuery.data && unmarkedRows.length === 0 && (
          <p className="flex items-center gap-1.5 rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300">
            <CheckCircle2 className="h-4 w-4" /> Tanlangan kun uchun barcha darslarning davomati olingan.
          </p>
        )}
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">Tarix</h2>
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
                <Th>O'quvchi</Th>
                <Th>Sinf</Th>
                <Th>Fan</Th>
                <Th>Holat</Th>
              </Tr>
            </Thead>
            <Tbody>
              {historyQuery.data.results.map((record) => (
                <Tr key={record.id}>
                  <Td className="text-slate-700 dark:text-slate-200">{record.lesson_date}</Td>
                  <Td className="text-slate-700 dark:text-slate-200">{record.student_name}</Td>
                  <Td className="text-slate-700 dark:text-slate-200">{record.school_class_name}</Td>
                  <Td className="text-slate-700 dark:text-slate-200">{record.subject_name}</Td>
                  <Td>
                    <Badge tone={STATUS_TONE[record.status]}>
                      {STATUS_LABEL[record.status] ?? record.status}
                    </Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        )}
      </div>
    </div>
  );
}
