import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ChevronLeft, Hourglass, Swords, Trophy } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PrimaryButton } from "../../components/form";
import { ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import type { DuelListItem, DuelQuestionItem } from "../../types";

export function StudentDuelTakingPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [error, setError] = useState<string | null>(null);

  const { data: duel } = useQuery({
    queryKey: ["duel", id],
    queryFn: async () => (await api.get<DuelListItem>(`/duels/${id}/`)).data,
    enabled: Boolean(id),
  });

  const { data: questions, isLoading, isError } = useQuery({
    queryKey: ["duel", id, "questions"],
    queryFn: async () => (await api.get<DuelQuestionItem[]>(`/duels/${id}/questions/`)).data,
    enabled: Boolean(id) && !duel?.i_have_submitted,
  });

  const submitMutation = useMutation({
    mutationFn: async () =>
      (
        await api.post<DuelListItem>(`/duels/${id}/submit/`, {
          answers: Object.entries(answers).map(([question, selected_option]) => ({
            question: Number(question),
            selected_option,
          })),
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["duels"] });
      queryClient.invalidateQueries({ queryKey: ["duel", id] });
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: unknown } })?.response?.data;
      setError(typeof detail === "string" ? detail : "Yuborishda xatolik yuz berdi.");
    },
  });

  const finished = submitMutation.data ?? (duel?.i_have_submitted ? duel : null);
  if (finished) return <DuelResult duel={finished} />;

  if (isLoading) return <LoadingState />;
  if (isError || !questions) return <ErrorState />;

  const allAnswered = questions.every((q) => answers[q.id] !== undefined);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div className="flex items-center gap-2">
        <Swords className="text-brand-600 dark:text-brand-400" size={20} />
        <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">Duel</h1>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          submitMutation.mutate();
        }}
        className="space-y-5"
      >
        {questions.map((question, index) => (
          <div
            key={question.id}
            className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"
          >
            <p className="font-medium text-slate-900 dark:text-slate-50">
              {index + 1}. {question.text}
            </p>
            <div className="mt-3 space-y-2">
              {question.options.map((option) => (
                <label
                  key={option.id}
                  className="flex cursor-pointer items-center gap-2 rounded-md border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50 has-[:checked]:border-brand-500 has-[:checked]:bg-brand-50 dark:border-slate-700 dark:hover:bg-slate-800 dark:has-[:checked]:bg-brand-500/10 dark:text-slate-200"
                >
                  <input
                    type="radio"
                    name={`question-${question.id}`}
                    checked={answers[question.id] === option.id}
                    onChange={() => setAnswers({ ...answers, [question.id]: option.id })}
                  />
                  {option.text}
                </label>
              ))}
            </div>
          </div>
        ))}

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

        <PrimaryButton type="submit" disabled={!allAnswered || submitMutation.isPending} className="w-full">
          {submitMutation.isPending ? "Yuborilmoqda..." : "Javoblarni yakunlash"}
        </PrimaryButton>
      </form>
    </div>
  );
}

function DuelResult({ duel }: { duel: DuelListItem }) {
  const opponentName = duel.my_role === "challenger" ? duel.opponent_name : duel.challenger_name;

  if (duel.status === "ACTIVE") {
    return (
      <div className="mx-auto max-w-lg space-y-4 text-center">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-8 dark:border-amber-500/30 dark:bg-amber-500/10">
          <Hourglass className="mx-auto h-8 w-8 text-amber-600 dark:text-amber-400" />
          <p className="mt-2 text-lg font-bold text-amber-700 dark:text-amber-300">Javobingiz qabul qilindi</p>
          <p className="mt-1 text-sm text-amber-700/80 dark:text-amber-300/80">
            {opponentName} hali javob bermadi — u topshirgach natija shu yerda chiqadi.
          </p>
        </div>
        <BackLink />
      </div>
    );
  }

  const won = duel.i_won;
  const isDraw = duel.result === "DRAW";
  const toneClass = isDraw
    ? "border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/60"
    : won
      ? "border-emerald-200 bg-emerald-50 dark:border-emerald-500/30 dark:bg-emerald-500/10"
      : "border-red-200 bg-red-50 dark:border-red-500/30 dark:bg-red-500/10";
  const textToneClass = isDraw
    ? "text-slate-700 dark:text-slate-200"
    : won
      ? "text-emerald-700 dark:text-emerald-400"
      : "text-red-700 dark:text-red-400";

  return (
    <div className="mx-auto max-w-lg space-y-4 text-center">
      <div className={`rounded-2xl border p-8 ${toneClass}`}>
        <Trophy className={`mx-auto h-8 w-8 ${textToneClass}`} />
        <p className={`mt-2 text-lg font-bold ${textToneClass}`}>
          {isDraw ? "Durang!" : won ? "G'alaba qozondingiz!" : "Bu safar omad yor bo'lmadi"}
        </p>
        <p className={`mt-1 text-sm ${textToneClass}`}>
          Siz: {duel.my_score_percent?.toFixed(0)}% · {opponentName}: {duel.opponent_score_percent?.toFixed(0)}%
        </p>
        <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
          Natijangiz asosida XP va duel reytingingiz avtomatik yangilandi.
        </p>
      </div>
      <BackLink />
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/student/duels"
      className="inline-flex items-center gap-0.5 text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
    >
      <ChevronLeft className="h-4 w-4" /> Duellar ro'yxatiga qaytish
    </Link>
  );
}
