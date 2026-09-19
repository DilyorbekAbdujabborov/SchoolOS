import { useMutation, useQuery } from "@tanstack/react-query";
import { BookOpen, Brain, Clock, Gamepad2, Swords } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "../../components/Badge";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import type { GameSession, GameType, Paginated, Subject } from "../../types";

const GAME_OPTIONS: { type: GameType; label: string; description: string; icon: typeof Swords }[] = [
  {
    type: "TUG_OF_WAR",
    label: "Arqon tortish",
    description: "Har to'g'ri javob arqonni o'zingizga tortadi — nechta savolga to'g'ri javob bera olasiz?",
    icon: Swords,
  },
  {
    type: "QUIZ",
    label: "Viktorina",
    description: "Klassik test-o'yin — savollarga javob bering, oxirida natijangizni ko'ring.",
    icon: Brain,
  },
];

export function StudentGamesPage() {
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState<number | null>(null);

  const { data: subjects, isLoading, isError } = useQuery({
    queryKey: ["subjects"],
    queryFn: async () => (await api.get<Paginated<Subject>>("/subjects/")).data,
  });

  const { data: history } = useQuery({
    queryKey: ["games"],
    queryFn: async () => (await api.get<Paginated<GameSession>>("/games/")).data,
  });

  const startGame = useMutation({
    mutationFn: async (game_type: GameType) =>
      (await api.post<GameSession>("/games/", { subject: selectedSubject, game_type })).data,
    onSuccess: (session) => navigate(`/student/games/${session.id}`),
  });

  return (
    <div className="space-y-6">
      <h1 className="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-slate-50">
        <Gamepad2 className="text-brand-600 dark:text-brand-400" size={20} />
        O'yinlar
      </h1>

      <div>
        <h2 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">1. Fan tanlang</h2>
        {isLoading && <LoadingState />}
        {isError && <ErrorState />}
        {subjects && subjects.results.length === 0 && <EmptyState title="Hali fan qo'shilmagan" />}
        {subjects && subjects.results.length > 0 && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {subjects.results.map((subject) => (
              <button
                key={subject.id}
                onClick={() => setSelectedSubject(subject.id)}
                className={`flex flex-col items-center gap-2 rounded-2xl border p-4 text-center transition-colors ${
                  selectedSubject === subject.id
                    ? "border-brand-500 bg-brand-50 dark:border-brand-400 dark:bg-brand-500/10"
                    : "border-slate-200 bg-white hover:border-brand-200 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-brand-500/30"
                }`}
              >
                <span
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${
                    selectedSubject === subject.id
                      ? "bg-brand-600 text-white"
                      : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400"
                  }`}
                >
                  <BookOpen size={18} />
                </span>
                <span className="text-sm font-medium text-slate-800 dark:text-slate-100">{subject.name}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedSubject && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">2. O'yinni tanlang</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {GAME_OPTIONS.map((option) => (
              <button
                key={option.type}
                onClick={() => startGame.mutate(option.type)}
                disabled={startGame.isPending}
                className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-5 text-left transition-colors hover:border-brand-300 hover:bg-brand-50/40 disabled:opacity-60 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-brand-500/30 dark:hover:bg-brand-500/5"
              >
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-400">
                  <option.icon size={20} />
                </span>
                <div>
                  <p className="font-semibold text-slate-900 dark:text-slate-50">{option.label}</p>
                  <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">{option.description}</p>
                </div>
              </button>
            ))}
          </div>
          {startGame.isPending && <LoadingState label="O'yin boshlanmoqda..." />}
        </div>
      )}

      {history && history.results.length > 0 && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">So'nggi o'yinlar</h2>
          <div className="divide-y divide-slate-100 rounded-2xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-slate-900">
            {history.results.slice(0, 8).map((session) => (
              <div key={session.id} className="flex items-center justify-between gap-3 px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {session.subject_name} · {session.game_type_display}
                  </p>
                  <p className="flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500">
                    <Clock size={11} />
                    {new Date(session.created_at).toLocaleDateString("uz-UZ")}
                  </p>
                </div>
                {session.status === "COMPLETED" ? (
                  <Badge tone="emerald">{session.score_percent?.toFixed(0)}%</Badge>
                ) : (
                  <Badge tone="amber">Tugallanmagan</Badge>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
