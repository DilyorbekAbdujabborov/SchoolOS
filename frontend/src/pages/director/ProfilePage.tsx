import { useQuery } from "@tanstack/react-query";
import { GraduationCap, School, Users } from "lucide-react";

import { ChangePasswordForm } from "../../components/ChangePasswordForm";
import { PageHeader } from "../../components/PageHeader";
import { ProfileHeaderCard } from "../../components/ProfileHeaderCard";
import { StatCard } from "../../components/StatCard";
import { TelegramConnect } from "../../components/TelegramConnect";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { DirectorDashboard } from "../../types";

export function DirectorProfilePage() {
  const { user } = useAuth();

  const { data } = useQuery({
    queryKey: ["dashboard", "director"],
    queryFn: async () => (await api.get<DirectorDashboard>("/dashboard/director/")).data,
  });

  const displayName = user ? `${user.first_name || user.username} ${user.last_name || ""}`.trim() : "";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Profil" />

      <ProfileHeaderCard
        name={displayName}
        email={user?.email}
        roleLabel="Direktor"
        stats={
          <>
            <StatCard label="O'quvchilar" value={data?.total_students ?? 0} icon={Users} tone="brand" />
            <StatCard label="O'qituvchilar" value={data?.total_teachers ?? 0} icon={GraduationCap} tone="violet" />
            <StatCard label="Sinflar" value={data?.total_classes ?? 0} icon={School} tone="amber" />
          </>
        }
      />

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
    </div>
  );
}
