import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Hourglass, Swords } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";

import {
  GameHeaderBar,
  GameInlineError,
  GameOptionButton,
  GameQuestionCard,
  GameResultScreen,
  GameStepProgress,
} from "../../components/games/GameUI";
import { PrimaryButton } from "../../components/form";
import { ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { DuelListItem, DuelQuestionItem } from "../../types";

export function StudentDuelTakingPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
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

  const answeredCount = Object.keys(answers).length;
  const allAnswered = questions.every((q) => answers[q.id] !== undefined);
  const opponentName = duel ? (duel.my_role === "challenger" ? duel.opponent_name : duel.challenger_name) : "";

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <GameHeaderBar
        title={opponentName ? `Duel · ${opponentName}` : "Duel"}
        totalXp={user?.total_xp ?? 0}
      />

      <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
        <span>
          Javob berildi {answeredCount}/{questions.length}
        </span>
      </div>
      <GameStepProgress index={answeredCount} total={questions.length} />

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setError(null);
          submitMutation.mutate();
        }}
        className="space-y-4"
      >
        {questions.map((question, index) => (
          <GameQuestionCard key={question.id}>
            <p className="font-semibold text-slate-900 dark:text-slate-50">
              {index + 1}. {question.text}
            </p>
            <div className="mt-4 space-y-2.5">
              {question.options.map((option, optionIndex) => (
                <GameOptionButton
                  key={option.id}
                  index={optionIndex}
                  text={option.text}
                  state={answers[question.id] === option.id ? "selected" : "default"}
                  onClick={() => setAnswers({ ...answers, [question.id]: option.id })}
                />
              ))}
            </div>
          </GameQuestionCard>
        ))}

        {error && <GameInlineError>{error}</GameInlineError>}

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
      <GameResultScreen
        tone="neutral"
        icon={Hourglass}
        title="Javobingiz qabul qilindi"
        subtitle={`${opponentName} hali javob bermadi — u topshirgach natija shu yerda chiqadi.`}
        stats={[]}
        secondaryTo="/student/duels"
        secondaryLabel="Duellar ro'yxatiga qaytish"
      />
    );
  }

  const isDraw = duel.result === "DRAW";
  const tone = isDraw ? "draw" : duel.i_won ? "win" : "lose";

  return (
    <GameResultScreen
      tone={tone}
      icon={Swords}
      title={isDraw ? "Durang!" : duel.i_won ? "G'alaba qozondingiz!" : "Bu safar omad yor bo'lmadi"}
      subtitle="Natijangiz asosida XP va duel reytingingiz avtomatik yangilandi."
      stats={[
        { label: "Siz", value: `${duel.my_score_percent?.toFixed(0) ?? 0}%` },
        { label: opponentName, value: `${duel.opponent_score_percent?.toFixed(0) ?? 0}%` },
      ]}
      secondaryTo="/student/duels"
      secondaryLabel="Duellar ro'yxatiga qaytish"
    />
  );
}
