import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, Flame, Minus, Pencil, Target } from "lucide-react";
import { useState } from "react";

import { Avatar } from "../../components/Avatar";
import { Input, PrimaryButton, SecondaryButton } from "../../components/form";
import { PageHeader } from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import type { LeagueBoard, LeagueMember, WeeklyGoalStatus } from "../../types";

/** "2026-01-05" → "05.01.2026". */
function formatDate(value: string): string {
  const [y, m, d] = value.split("-");
  return `${d}.${m}.${y}`;
}

/** Weekly XP goal with a progress bar and a streak of weeks hit. */
function WeeklyGoalCard() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [target, setTarget] = useState("");

  const { data, isLoading, isError } = useQuery({
    queryKey: ["weekly-goal"],
    queryFn: async () => (await api.get<WeeklyGoalStatus>("/weekly-goal/")).data,
  });

  const save = useMutation({
    mutationFn: async () =>
      (await api.patch<WeeklyGoalStatus>("/weekly-goal/", { target_xp: Number(target) })).data,
    onSuccess: (updated) => {
      queryClient.setQueryData(["weekly-goal"], updated);
      setEditing(false);
    },
  });

  if (isLoading) return <LoadingState />;
  if (isError || !data) return <ErrorState />;

  const pct = data.target_xp > 0 ? Math.min(100, Math.round((data.earned_xp / data.target_xp) * 100)) : 0;

  return (
    <section className="card p-6">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <Target className="h-5 w-5 text-brand-600 dark:text-brand-400" />
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">
            Haftalik maqsad
          </h2>
        </div>
        {data.goal_streak > 0 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:bg-amber-950/40 dark:text-amber-400">
            <Flame className="h-3.5 w-3.5" /> {data.goal_streak} hafta ketma-ket
          </span>
        )}
      </div>

      <div className="mt-4 flex items-end justify-between">
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Bu hafta{" "}
          <span className="font-semibold text-slate-900 dark:text-slate-100">{data.earned_xp} XP</span> /{" "}
          {data.target_xp} XP
        </p>
        {!editing && (
          <button
            type="button"
            onClick={() => {
              setTarget(String(data.target_xp));
              setEditing(true);
            }}
            className="inline-flex items-center gap-1 text-xs font-medium text-brand-600 hover:underline dark:text-brand-400"
          >
            <Pencil className="h-3.5 w-3.5" /> Maqsadni o'zgartirish
          </button>
        )}
      </div>

      <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-surface-raised">
        <div
          className={`h-full rounded-full transition-all ${data.met ? "bg-emerald-500" : "bg-brand-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
        {data.met
          ? "Maqsadga yetdingiz! 🎉"
          : `Maqsadgacha yana ${data.target_xp - data.earned_xp} XP`}{" "}
        · Yangilanish: {formatDate(data.resets_on)} (Dushanba)
        {data.best_goal_streak > 0 && ` · Rekord: ${data.best_goal_streak} hafta`}
      </p>

      {editing && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            save.mutate();
          }}
          className="mt-4 flex items-end gap-2"
        >
          <label className="flex-1">
            <span className="mb-1 block text-xs font-medium text-ink-muted">Haftalik XP maqsadi</span>
            <Input
              type="number"
              min={50}
              max={100000}
              step={50}
              required
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="py-2"
            />
          </label>
          <PrimaryButton type="submit" disabled={save.isPending}>
            {save.isPending ? "..." : "Saqlash"}
          </PrimaryButton>
          <SecondaryButton type="button" onClick={() => setEditing(false)}>
            Bekor
          </SecondaryButton>
        </form>
      )}
    </section>
  );
}

const ZONE_ROW: Record<LeagueMember["zone"], string> = {
  up: "border-l-2 border-emerald-500 bg-emerald-50/40 dark:bg-emerald-950/20",
  down: "border-l-2 border-rose-400 bg-rose-50/40 dark:bg-rose-950/20",
  stay: "border-l-2 border-transparent",
};

function ZoneIcon({ zone }: { zone: LeagueMember["zone"] }) {
  if (zone === "up") return <ChevronUp className="h-4 w-4 text-emerald-500" />;
  if (zone === "down") return <ChevronDown className="h-4 w-4 text-rose-400" />;
  return <Minus className="h-4 w-4 text-slate-300 dark:text-slate-600" />;
}

export function StudentLeaguePage() {
  const [tier, setTier] = useState<number | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["league", tier],
    queryFn: async () =>
      (await api.get<LeagueBoard>("/league/", { params: tier ? { tier } : {} })).data,
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Liga" subtitle="Har hafta XP bo'yicha poyga — dushanba kuni yangilanadi." />

      <WeeklyGoalCard />

      {/* Tier chips */}
      {data && (
        <div className="flex gap-2 overflow-x-auto pb-1">
          {data.tiers.map((t) => {
            const active = t.tier === data.tier;
            return (
              <button
                key={t.tier}
                type="button"
                onClick={() => setTier(t.tier)}
                className={`flex shrink-0 select-none items-center gap-1.5 rounded-xl border px-3 py-2 text-sm transition-colors ${
                  active
                    ? "border-brand-600 bg-brand-600 text-white shadow-sm"
                    : "border-line bg-surface text-ink-muted hover:bg-surface-raised"
                }`}
              >
                <span>{t.icon}</span>
                <span className="font-medium">{t.name.replace(" liga", "")}</span>
                <span className={`text-xs ${active ? "text-white/70" : "text-slate-400"}`}>
                  {t.count}
                </span>
                {t.is_mine && (
                  <span
                    className={`rounded-full px-1.5 text-[10px] font-semibold ${
                      active ? "bg-white/20" : "bg-brand-100 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                    }`}
                  >
                    Siz
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}

      {data && (
        <section className="card overflow-hidden">
          {/* Board header */}
          <div className="flex items-center gap-4 border-b border-line p-6">
            <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-surface-raised text-3xl">
              {data.tier_icon}
            </div>
            <div className="min-w-0">
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-50">{data.tier_name}</h2>
              {data.tier === data.my_tier && data.my_rank ? (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Bu hafta <span className="font-semibold">{data.my_weekly_xp} XP</span> ·{" "}
                  {data.my_rank}-o'rin
                </p>
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">{data.members.length} o'quvchi</p>
              )}
              <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">
                Hafta yakuni: {formatDate(data.resets_on)} (Dushanba) — o'shanda ligalar yangilanadi.
              </p>
            </div>
          </div>

          {/* Zone legend */}
          {(data.promote_count > 0 || data.demote_count > 0) && (
            <div className="flex flex-wrap gap-4 border-b border-line bg-surface-raised/50 px-6 py-2.5 text-xs text-slate-500 dark:text-slate-400">
              {data.promote_count > 0 && (
                <span className="inline-flex items-center gap-1">
                  <ChevronUp className="h-3.5 w-3.5 text-emerald-500" /> Yuqori {data.promote_count} —
                  ko'tariladi
                </span>
              )}
              {data.demote_count > 0 && (
                <span className="inline-flex items-center gap-1">
                  <ChevronDown className="h-3.5 w-3.5 text-rose-400" /> Past {data.demote_count} — tushadi
                </span>
              )}
            </div>
          )}

          {/* Members */}
          {data.members.length === 0 ? (
            <p className="p-6 text-sm text-slate-400 dark:text-slate-500">
              Bu ligada hali o'quvchi yo'q.
            </p>
          ) : (
            <ul>
              {data.members.map((member) => (
                <li
                  key={member.rank}
                  className={`flex items-center gap-3 px-6 py-3 ${ZONE_ROW[member.zone]} ${
                    member.is_me ? "bg-brand-50/60 dark:bg-brand-950/30" : ""
                  }`}
                >
                  <span className="w-5 shrink-0">
                    <ZoneIcon zone={member.zone} />
                  </span>
                  <span className="tabular w-6 shrink-0 text-sm font-semibold text-ink-subtle">
                    {member.rank}
                  </span>
                  <Avatar name={member.name} src={member.avatar_url} size={36} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">
                      {member.name}
                      {member.is_me && (
                        <span className="ml-2 rounded-full bg-brand-100 px-1.5 py-0.5 text-[10px] font-semibold text-brand-700 dark:bg-brand-950 dark:text-brand-300">
                          Siz
                        </span>
                      )}
                    </p>
                    {member.school_class_name && (
                      <p className="truncate text-xs text-slate-400 dark:text-slate-500">
                        {member.school_class_name}
                      </p>
                    )}
                  </div>
                  <span className="tabular shrink-0 text-sm font-semibold text-slate-700 dark:text-slate-200">
                    {member.weekly_xp} XP
                  </span>
                </li>
              ))}
            </ul>
          )}

          <p className="border-t border-line bg-surface-raised/50 px-6 py-3 text-xs text-slate-500 dark:text-slate-400">
            XP yig'gan sari yuqori ligaga ko'tarilasiz. Har hafta dushanba kuni poyga qaytadan
            boshlanadi. Jadval real vaqtda yangilanib turadi.
          </p>
        </section>
      )}
    </div>
  );
}
