import { useQuery } from "@tanstack/react-query";
import { BarChart3, Flame, Trophy } from "lucide-react";

import { ChangePasswordForm } from "../../components/ChangePasswordForm";
import { ParentTelegramConnect } from "../../components/ParentTelegramConnect";
import { PageHeader } from "../../components/PageHeader";
import { ProfileHeaderCard } from "../../components/ProfileHeaderCard";
import { ProgressBar } from "../../components/ProgressBar";
import { StatCard } from "../../components/StatCard";
import { TelegramConnect } from "../../components/TelegramConnect";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { getLevelInfo } from "../../lib/gamification";
import type { MyRank, Streak } from "../../types";

export function StudentProfilePage() {
  const { user } = useAuth();

  const { data: streak } = useQuery({
    queryKey: ["streak", "me"],
    queryFn: async () => (await api.get<Streak>("/streaks/me/")).data,
  });
  const { data: rank } = useQuery({
    queryKey: ["rank", "me"],
    queryFn: async () => (await api.get<MyRank>("/leaderboard/me/")).data,
  });

  const displayName = user ? `${user.first_name || user.username} ${user.last_name || ""}`.trim() : "";
  const { level, xpIntoLevel, xpForNextLevel, progressPercent } = getLevelInfo(user?.total_xp ?? 0);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Profil" />

      <ProfileHeaderCard
        name={displayName}
        email={user?.email}
        roleLabel="O'quvchi"
        stats={
          <>
            <StatCard label="Daraja" value={level} icon={Trophy} tone="brand" />
            <StatCard label="Seriya" value={streak?.current_streak ?? 0} icon={Flame} tone="amber" />
            <StatCard
              label="Sinf reytingi"
              value={rank?.class_rank ? `#${rank.class_rank}` : "—"}
              icon={BarChart3}
              tone="emerald"
            />
          </>
        }
      />

      <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-2 flex items-center justify-between text-sm">
          <span className="font-semibold text-slate-700 dark:text-slate-200">{level}-daraja</span>
          <span className="text-slate-500 dark:text-slate-400">
            {xpIntoLevel} / {xpForNextLevel} XP
          </span>
        </div>
        <ProgressBar value={progressPercent} tone="brand" />
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-3 font-semibold text-slate-900 dark:text-slate-50">Hisob ma'lumotlari</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500 dark:text-slate-400">Email</dt>
              <dd className="truncate text-slate-800 dark:text-slate-100">{user?.email}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500 dark:text-slate-400">Login</dt>
              <dd className="truncate text-slate-800 dark:text-slate-100">{user?.username}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500 dark:text-slate-400">Jami XP</dt>
              <dd className="text-slate-800 dark:text-slate-100">{user?.total_xp ?? 0}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="mb-3 font-semibold text-slate-900 dark:text-slate-50">Parolni o'zgartirish</h2>
          <ChangePasswordForm />
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="mb-3 font-semibold text-slate-900 dark:text-slate-50">Telegram</h2>
        <TelegramConnect />
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
        <h2 className="mb-3 font-semibold text-slate-900 dark:text-slate-50">Ota-onani Telegramga ulash</h2>
        <ParentTelegramConnect />
      </div>
    </div>
  );
}
