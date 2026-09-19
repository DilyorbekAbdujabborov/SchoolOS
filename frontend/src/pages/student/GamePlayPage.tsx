import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Brain, ChevronLeft, Swords, Trophy } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PrimaryButton } from "../../components/form";
import { LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import type { GameQuestion, GameSession } from "../../types";

/** 0 = fully pulled to the student's side, 100 = fully pulled to the AI's side. */
function RopeTrack({ position }: { position: number }) {
  const clamped = Math.min(100, Math.max(0, position));
  return (
    <div className="relative my-6 h-3 rounded-full bg-gradient-to-r from-brand-200 via-slate-200 to-red-200 dark:from-brand-500/30 dark:via-slate-700 dark:to-red-500/30">
      <div
        className="absolute top-1/2 h-7 w-7 -translate-y-1/2 rounded-full border-4 border-white bg-amber-500 shadow-md transition-all duration-1000 ease-out dark:border-slate-900"
        style={{ left: `calc(${clamped}% - 14px)` }}
      />
    </div>
  );
}

export function StudentGamePlayPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [ropePosition, setRopePosition] = useState(50);

  const { data: session } = useQuery({
    queryKey: ["game", id],
    queryFn: async () => (await api.get<GameSession>(`/games/${id}/`)).data,
    enabled: Boolean(id),
  });

  const questionsQuery = useQuery({
    queryKey: ["game", id, "questions"],
    queryFn: async () => (await api.get<GameQuestion[]>(`/games/${id}/questions/`)).data,
    enabled: Boolean(id) && session?.status === "ACTIVE",
    retry: false,
  });

  const submitMutation = useMutation({
    mutationFn: async (finalAnswers: Record<number, number>) =>
      (
        await api.post<GameSession>(`/games/${id}/submit/`, {
          answers: Object.entries(finalAnswers).map(([question_index, selected_index]) => ({
            question_index: Number(question_index),
            selected_index,
          })),
        })
      ).data,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      queryClient.setQueryData(["game", id], result);
      setTimeout(() => setRopePosition(100 - (result.score_percent ?? 0)), 50);
    },
  });

  if (!session) return <LoadingState />;

  const finished = submitMutation.data ?? (session.status === "COMPLETED" ? session : null);
  if (finished) return <GameResult session={finished} ropePosition={ropePosition} />;

  const isTugOfWar = session.game_type === "TUG_OF_WAR";
  const GameIcon = isTugOfWar ? Swords : Brain;

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <div className="flex items-center gap-2">
        <GameIcon className="text-brand-600 dark:text-brand-400" size={20} />
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">
          {session.subject_name} — {session.game_type_display}
        </h1>
      </div>

      <div className="flex items-center justify-between text-sm font-medium text-slate-600 dark:text-slate-300">
        <span>
          {Math.min(questionIndex + 1, questionsQuery.data?.length ?? 1)} / {questionsQuery.data?.length ?? "…"}
        </span>
      </div>
      {isTugOfWar && <RopeTrack position={50} />}

      {questionsQuery.isLoading && <LoadingState label="O'yin tayyorlanmoqda..." />}
      {questionsQuery.isError && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-center dark:border-red-500/30 dark:bg-red-500/10">
          <p className="text-sm text-red-700 dark:text-red-300">
            AI hozircha javob bera olmadi. Birozdan so'ng qayta urinib ko'ring.
          </p>
          <PrimaryButton className="mt-3" onClick={() => questionsQuery.refetch()}>
            Qayta urinish
          </PrimaryButton>
        </div>
      )}
      {questionsQuery.data?.[questionIndex] && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <p className="font-medium text-slate-900 dark:text-slate-50">
            {questionsQuery.data[questionIndex].text}
          </p>
          <div className="mt-3 space-y-2">
            {questionsQuery.data[questionIndex].options.map((option, optionIndex) => (
              <button
                key={option}
                onClick={() => {
                  const questions = questionsQuery.data!;
                  const isLast = questionIndex === questions.length - 1;
                  const nextAnswers = { ...answers, [questionIndex]: optionIndex };
                  setAnswers(nextAnswers);
                  if (isLast) {
                    submitMutation.mutate(nextAnswers);
                  } else {
                    setQuestionIndex((i) => i + 1);
                  }
                }}
                className="flex w-full items-center rounded-md border border-slate-200 px-3 py-2 text-left text-sm hover:border-brand-500 hover:bg-brand-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-brand-500/10"
              >
                {option}
              </button>
            ))}
          </div>
        </div>
      )}
      {submitMutation.isPending && <LoadingState label="Natija hisoblanmoqda..." />}
    </div>
  );
}

function GameResult({ session, ropePosition }: { session: GameSession; ropePosition: number }) {
  const score = session.score_percent ?? 0;
  const won = score >= 50;
  const toneClass = won
    ? "border-emerald-200 bg-emerald-50 dark:border-emerald-500/30 dark:bg-emerald-500/10"
    : "border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/60";
  const textToneClass = won ? "text-emerald-700 dark:text-emerald-400" : "text-slate-700 dark:text-slate-200";

  return (
    <div className="mx-auto max-w-xl space-y-4 text-center">
      {session.game_type === "TUG_OF_WAR" && <RopeTrack position={ropePosition} />}
      <div className={`rounded-2xl border p-8 ${toneClass}`}>
        <Trophy className={`mx-auto h-8 w-8 ${textToneClass}`} />
        <p className={`mt-2 text-lg font-bold ${textToneClass}`}>
          {won ? "Zo'r natija!" : "Yana urinib ko'ring!"}
        </p>
        <p className={`mt-1 text-sm ${textToneClass}`}>
          Natija: {score.toFixed(0)}%{session.xp_awarded ? ` · +${session.xp_awarded} XP` : ""}
        </p>
      </div>
      <Link
        to="/student/games"
        className="inline-flex items-center gap-0.5 text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
      >
        <ChevronLeft className="h-4 w-4" /> O'yinlar ro'yxatiga qaytish
      </Link>
    </div>
  );
}
