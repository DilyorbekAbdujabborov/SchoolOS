import { useQuery } from "@tanstack/react-query";
import { Crown, Medal, Trophy, Users } from "lucide-react";
import { useState } from "react";

import { api } from "../lib/api";
import { TONE_DOT, TONE_FILL, type Tone } from "../lib/tones";
import type { ClassLeaderboardEntry, StudentLeaderboardEntry } from "../types";
import { Avatar } from "./Avatar";
import { SegmentedControl } from "./form";
import { EmptyState, ErrorState, TableSkeleton } from "./states";

/** Top three get a medal and a real hue; everyone else is just a number. */
const MEDAL_TONE: Record<number, Tone> = { 1: "amber", 2: "slate", 3: "violet" };

function RankBadge({ rank }: { rank: number }) {
  const tone = MEDAL_TONE[rank];
  return (
    <span className="inline-flex h-7 w-7 items-center justify-center">
      {tone ? (
        <span
          className={`flex h-7 w-7 items-center justify-center rounded-lg ${TONE_DOT[tone]}`}
        >
          {rank === 1 ? (
            <Crown size={14} className="text-white" />
          ) : (
            <span className="tabular text-xs font-bold text-white">{rank}</span>
          )}
        </span>
      ) : (
        <span className="tabular text-sm font-semibold text-ink-subtle">{rank}</span>
      )}
    </span>
  );
}

export function Leaderboard() {
  const [tab, setTab] = useState<"students" | "classes">("students");

  const studentsQuery = useQuery({
    queryKey: ["leaderboard", "students"],
    queryFn: async () => (await api.get<StudentLeaderboardEntry[]>("/leaderboard/students/")).data,
    enabled: tab === "students",
  });
  const classesQuery = useQuery({
    queryKey: ["leaderboard", "classes"],
    queryFn: async () => (await api.get<ClassLeaderboardEntry[]>("/leaderboard/classes/")).data,
    enabled: tab === "classes",
  });

  const query = tab === "students" ? studentsQuery : classesQuery;

  return (
    <div className="space-y-4">
      <SegmentedControl
        value={tab}
        onChange={setTab}
        options={[
          {
            value: "students",
            label: (
              <span className="flex items-center gap-1.5">
                <Users size={14} /> O'quvchilar
              </span>
            ),
          },
          {
            value: "classes",
            label: (
              <span className="flex items-center gap-1.5">
                <Trophy size={14} /> Sinflar
              </span>
            ),
          },
        ]}
      />

      {query.isLoading && <TableSkeleton rows={6} cols={4} />}
      {query.isError && <ErrorState />}
      {query.data && query.data.length === 0 && (
        <EmptyState
          title="Reyting hali bo'sh"
          description="XP berilgach, o'quvchilar va sinflar reytingi shu yerda paydo bo'ladi."
          icon={Medal}
        />
      )}

      {query.data && query.data.length > 0 && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-left text-sm">
              <thead className="border-b border-line bg-surface-raised text-ink-subtle">
                <tr>
                  <th className="w-14 px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.06em]">
                    O'rin
                  </th>
                  <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.06em]">
                    Nomi
                  </th>
                  {tab === "students" && (
                    <th className="px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.06em]">
                      Sinf
                    </th>
                  )}
                  <th className="px-4 py-2.5 text-right text-[11px] font-semibold uppercase tracking-[0.06em]">
                    XP
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line-soft">
                {tab === "students"
                  ? (studentsQuery.data ?? []).map((entry) => (
                      <tr
                        key={entry.rank}
                        className="transition-colors duration-150 hover:bg-surface-raised/70"
                      >
                        <td className="px-4 py-3">
                          <RankBadge rank={entry.rank} />
                        </td>
                        <td className="px-4 py-3">
                          <span className="flex items-center gap-3">
                            <Avatar name={entry.name} src={entry.avatar_url} size={30} />
                            <span className="font-medium text-ink">{entry.name}</span>
                          </span>
                        </td>
                        <td className="px-4 py-3 text-ink-muted">
                          {entry.school_class_name ?? "—"}
                        </td>
                        <td className="tabular px-4 py-3 text-right font-semibold text-ink">
                          {entry.total_xp}
                        </td>
                      </tr>
                    ))
                  : (classesQuery.data ?? []).map((entry) => (
                      <tr
                        key={entry.rank}
                        className="transition-colors duration-150 hover:bg-surface-raised/70"
                      >
                        <td className="px-4 py-3">
                          <RankBadge rank={entry.rank} />
                        </td>
                        <td className="px-4 py-3 font-medium text-ink">{entry.name}</td>
                        <td className="tabular px-4 py-3 text-right font-semibold text-ink">
                          {entry.total_xp}
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/** A three-up podium used on dashboards: 2nd, 1st, 3rd. */
export function LeaderboardPodium({ entries }: { entries: StudentLeaderboardEntry[] }) {
  const top = entries.slice(0, 3);
  if (top.length === 0) return null;
  const order = [top[1], top[0], top[2]].filter(Boolean) as StudentLeaderboardEntry[];
  const height: Record<number, string> = { 1: "h-16", 2: "h-11", 3: "h-9" };
  const tone: Record<number, Tone> = { 1: "amber", 2: "slate", 3: "violet" };

  return (
    <div className="flex items-end justify-center gap-2 sm:gap-3">
      {order.map((entry) => (
        <div key={entry.rank} className="flex flex-1 flex-col items-center gap-1.5">
          <Avatar name={entry.name} src={entry.avatar_url} size={entry.rank === 1 ? 44 : 34} />
          <p className="max-w-full truncate text-xs font-medium text-ink">{entry.name}</p>
          <div
            className={`flex w-full items-start justify-center rounded-t-xl pt-1.5 text-[11px] font-bold text-white ${
              height[entry.rank]
            } ${TONE_FILL[tone[entry.rank]]}`}
          >
            {entry.rank}
          </div>
        </div>
      ))}
    </div>
  );
}
