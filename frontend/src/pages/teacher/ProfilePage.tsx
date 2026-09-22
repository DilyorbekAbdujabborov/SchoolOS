import { useQuery } from "@tanstack/react-query";
import { ClipboardList, FileText, Users } from "lucide-react";

import { ChangePasswordForm } from "../../components/ChangePasswordForm";
import { PageHeader } from "../../components/PageHeader";
import { ProfileHeaderCard } from "../../components/ProfileHeaderCard";
import { StatCard } from "../../components/StatCard";
import { TelegramConnect } from "../../components/TelegramConnect";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { ActivitySummary, Paginated, TeacherDashboard, TestSummary } from "../../types";

export function TeacherProfilePage() {
  const { user } = useAuth();

  const { data } = useQuery({
    queryKey: ["dashboard", "teacher"],
    queryFn: async () => (await api.get<TeacherDashboard>("/dashboard/teacher/")).data,
  });
  const { data: tests } = useQuery({
    queryKey: ["tests", "teacher"],
    queryFn: async () => (await api.get<Paginated<TestSummary>>("/tests/")).data,
  });
  const { data: activities } = useQuery({
    queryKey: ["activities", "teacher"],
    queryFn: async () => (await api.get<Paginated<ActivitySummary>>("/activities/")).data,
  });

  const displayName = user ? `${user.first_name || user.username} ${user.last_name || ""}`.trim() : "";

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Profil" />

      <ProfileHeaderCard
        name={displayName}
        email={user?.email}
        roleLabel="O'qituvchi"
        stats={
          <>
            <StatCard label="Sinflarim" value={data?.my_classes_count ?? 0} icon={Users} tone="brand" />
            <StatCard label="Testlarim" value={tests?.results.length ?? 0} icon={FileText} tone="violet" />
            <StatCard label="Topshiriqlarim" value={activities?.results.length ?? 0} icon={ClipboardList} tone="amber" />
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
