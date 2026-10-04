import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Field, Input, PrimaryButton } from "../../components/form";
import { PageHeader } from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/states";
import { TelegramConnect } from "../../components/TelegramConnect";
import { api } from "../../lib/api";
import type { SchoolTimeConfig } from "../../types";

/** ISO weekday → short Uzbek label, in week order (Mon first). */
const WEEKDAYS = [
  { value: 1, label: "Dush" },
  { value: 2, label: "Sesh" },
  { value: 3, label: "Chor" },
  { value: 4, label: "Pay" },
  { value: 5, label: "Juma" },
  { value: 6, label: "Shan" },
  { value: 7, label: "Yak" },
];

export function SettingsPage() {
  const queryClient = useQueryClient();
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [periodDuration, setPeriodDuration] = useState("45");
  const [shortBreak, setShortBreak] = useState("5");
  const [longBreakAfterPeriod, setLongBreakAfterPeriod] = useState("4");
  const [longBreak, setLongBreak] = useState("20");
  const [schoolDays, setSchoolDays] = useState<number[]>([1, 2, 3, 4, 5, 6]);
  const [saved, setSaved] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["school-config"],
    queryFn: async () => (await api.get<SchoolTimeConfig>("/school-config/")).data,
  });

  useEffect(() => {
    if (data) {
      setStartTime(data.start_time.slice(0, 5));
      setEndTime(data.end_time.slice(0, 5));
      setPeriodDuration(String(data.period_duration_minutes));
      setShortBreak(String(data.short_break_minutes));
      setLongBreakAfterPeriod(String(data.long_break_after_period));
      setLongBreak(String(data.long_break_minutes));
      if (Array.isArray(data.school_days)) setSchoolDays(data.school_days);
    }
  }, [data]);

  function toggleDay(day: number) {
    setSchoolDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort((a, b) => a - b),
    );
  }

  const save = useMutation({
    mutationFn: async () =>
      (
        await api.patch("/school-config/", {
          start_time: `${startTime}:00`,
          end_time: `${endTime}:00`,
          period_duration_minutes: Number(periodDuration),
          short_break_minutes: Number(shortBreak),
          long_break_after_period: Number(longBreakAfterPeriod),
          long_break_minutes: Number(longBreak),
          school_days: schoolDays,
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["school-config"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Sozlamalar" subtitle="Maktab vaqti, dars jadvali va bog'lanish sozlamalari." />

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}

      {data && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
          className="space-y-6"
        >
          <section className="card p-7">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">
              Dars vaqti (School Time Lock)
            </h2>
            <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
              Shu vaqt oralig'ida o'quvchilar platformadan foydalana olmaydi. Direktor va
              o'qituvchilarga bu cheklov taalluqli emas.
            </p>
            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Boshlanishi">
                <Input
                  type="time"
                  required
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="py-2.5"
                />
              </Field>
              <Field label="Tugashi">
                <Input
                  type="time"
                  required
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="py-2.5"
                />
              </Field>
            </div>

            <div className="mt-5">
              <span className="mb-2 block text-sm font-medium text-ink-muted">Dars kunlari</span>
              <p className="mb-3 text-xs text-slate-500 dark:text-slate-400">
                Cheklov faqat tanlangan kunlarda ishlaydi. Dam olish kunlari (masalan yakshanba)
                platforma ochiq bo'ladi.
              </p>
              <div className="flex flex-wrap gap-2">
                {WEEKDAYS.map((weekday) => {
                  const active = schoolDays.includes(weekday.value);
                  return (
                    <button
                      key={weekday.value}
                      type="button"
                      onClick={() => toggleDay(weekday.value)}
                      aria-pressed={active}
                      className={`select-none rounded-lg border px-3.5 py-2 text-sm font-medium transition-colors ${
                        active
                          ? "border-brand-600 bg-brand-600 text-white shadow-sm"
                          : "border-line bg-surface text-ink-muted hover:bg-surface-raised"
                      }`}
                    >
                      {weekday.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </section>

          <section className="card p-7">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Dars jadvali vaqtlari</h2>
            <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
              Har bir dars va tanaffus necha daqiqa davom etishi. "Darslarni yaratish" tugmasi
              shu qiymatlarga qarab har bir darsning vaqtini hisoblaydi.
            </p>
            <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field label="Dars davomiyligi (daqiqa)">
                <Input
                  type="number"
                  min={1}
                  required
                  value={periodDuration}
                  onChange={(e) => setPeriodDuration(e.target.value)}
                  className="py-2.5"
                />
              </Field>
              <Field label="Kichik tanaffus (daqiqa)">
                <Input
                  type="number"
                  min={0}
                  required
                  value={shortBreak}
                  onChange={(e) => setShortBreak(e.target.value)}
                  className="py-2.5"
                />
              </Field>
              <Field label="Katta tanaffus qaysi darsdan keyin">
                <Input
                  type="number"
                  min={1}
                  required
                  value={longBreakAfterPeriod}
                  onChange={(e) => setLongBreakAfterPeriod(e.target.value)}
                  className="py-2.5"
                />
              </Field>
              <Field label="Katta tanaffus (daqiqa)">
                <Input
                  type="number"
                  min={0}
                  required
                  value={longBreak}
                  onChange={(e) => setLongBreak(e.target.value)}
                  className="py-2.5"
                />
              </Field>
            </div>
          </section>

          <div className="flex items-center gap-3">
            <PrimaryButton type="submit" disabled={save.isPending}>
              {save.isPending ? "Saqlanmoqda..." : "Saqlash"}
            </PrimaryButton>
            {saved && (
              <span className="inline-flex items-center gap-1.5 text-sm text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-4 w-4" /> Saqlandi
              </span>
            )}
          </div>
        </form>
      )}

      <section className="card p-7">
        <h2 className="mb-3 text-base font-semibold text-slate-900 dark:text-slate-50">Telegram</h2>
        <TelegramConnect />
      </section>
    </div>
  );
}
