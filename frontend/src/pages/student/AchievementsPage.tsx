import { useQuery } from "@tanstack/react-query";
import { Lock, Zap } from "lucide-react";

import { PageHeader } from "../../components/PageHeader";
import { ProgressBar } from "../../components/ProgressBar";
import { ErrorState, LoadingState } from "../../components/states";
import { AchievementIcon } from "../../lib/achievementIcons";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { Achievement, AchievementConditionType, Streak } from "../../types";

/** Only these two condition types have a number the student can already see
 * live elsewhere in the app (their own XP total, their own streak) — showing
 * a progress bar for the rest would mean guessing at a count the API doesn't
 * expose per-achievement, so those stay a plain locked state instead. */
const PROGRESS_SOURCE: Partial<Record<AchievementConditionType, "xp" | "streak">> = {
  XP_THRESHOLD: "xp",
  STREAK_LENGTH: "streak",
};

export function StudentAchievementsPage() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["achievements"],
    queryFn: async () => (await api.get<Achievement[]>("/achievements/")).data,
  });
  const { data: streak } = useQuery({
    queryKey: ["streak", "me"],
    queryFn: async () => (await api.get<Streak>("/streaks/me/")).data,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Yutuqlarim"
        subtitle={data ? `${data.filter((a) => a.unlocked).length} / ${data.length} yutuq ochilgan` : undefined}
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}

      {data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {data.map((achievement) => (
            <div
              key={achievement.id}
              className={`hover-card rounded-2xl border p-5 text-center ${
                achievement.unlocked
                  ? "border-amber-200 bg-amber-50 dark:border-amber-500/30 dark:bg-amber-500/10"
                  : "border-slate-200 bg-slate-50 opacity-80 dark:border-slate-800 dark:bg-slate-800/60"
              }`}
            >
              <span
                className={`mx-auto flex h-12 w-12 items-center justify-center rounded-full ${
                  achievement.unlocked
                    ? "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300"
                    : "bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500"
                }`}
              >
                {achievement.unlocked ? (
                  <AchievementIcon icon={achievement.icon} className="h-6 w-6" />
                ) : (
                  <Lock className="h-5 w-5" />
                )}
              </span>
              <p className="mt-2 font-semibold text-slate-900 dark:text-slate-50">{achievement.name}</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{achievement.description}</p>

              {!achievement.unlocked &&
                (() => {
                  const source = PROGRESS_SOURCE[achievement.condition_type];
                  if (!source) return null;
                  const current = source === "xp" ? (user?.total_xp ?? 0) : (streak?.current_streak ?? 0);
                  const target = achievement.condition_value;
                  const percent = target > 0 ? Math.min(100, (current / target) * 100) : 0;
                  return (
                    <div className="mt-3">
                      <ProgressBar value={percent} tone="brand" className="h-1.5" />
                      <p className="mt-1 text-[11px] text-slate-400 dark:text-slate-500">
                        {Math.min(current, target)} / {target}
                      </p>
                    </div>
                  );
                })()}

              {achievement.xp_reward > 0 && (
                <span className="mt-2 inline-flex items-center gap-1 rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
                  <Zap size={11} />+{achievement.xp_reward} XP
                </span>
              )}

              {achievement.unlocked && achievement.unlocked_at && (
                <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">
                  {new Date(achievement.unlocked_at).toLocaleDateString("uz-UZ")}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
