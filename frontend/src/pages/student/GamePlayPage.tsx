import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { BattleArenaGame } from "../../components/games/BattleArenaGame";
import { CodeBreakerGame } from "../../components/games/CodeBreakerGame";
import { NeonRacingGame } from "../../components/games/NeonRacingGame";
import { TowerDefenseGame } from "../../components/games/TowerDefenseGame";
import { TreasureHuntGame } from "../../components/games/TreasureHuntGame";
import { TowerBuilderGame } from "../../components/games/TowerBuilderGame";
import { TugOfWarGame } from "../../components/games/TugOfWarGame";
import {
  AnimatedNumber,
  GameHeaderBar,
  GameInlineError,
  GameOptionButton,
  GameQuestionCard,
  GameResultScreen,
  GameStepProgress,
} from "../../components/games/GameUI";
import { PrimaryButton } from "../../components/form";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { isNoQuestionsError, NO_QUESTIONS_HINT, NO_QUESTIONS_TITLE } from "../../lib/gameErrors";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import type { GameQuestion, GameSession } from "../../types";

export function StudentGamePlayPage() {
  const { id } = useParams<{ id: string }>();

  const { data: session, isError } = useQuery({
    queryKey: ["game", id],
    queryFn: async () => (await api.get<GameSession>(`/games/${id}/`)).data,
    enabled: Boolean(id),
    retry: false,
  });

  if (isError) return <ErrorState message="O'yin topilmadi yoki yuklanmadi." />;
  if (!session) return <LoadingState />;

  if (session.game_type === "TUG_OF_WAR") {
    return <TugOfWarGame session={session} />;
  }

  if (session.game_type === "TOWER_BUILDER") {
    return <TowerBuilderGame session={session} />;
  }

  if (session.game_type === "CODE_BREAKER") {
    return <CodeBreakerGame session={session} />;
  }

  if (session.game_type === "TREASURE_HUNT") {
    return <TreasureHuntGame session={session} />;
  }

  if (session.game_type === "NEON_RACING") {
    return <NeonRacingGame session={session} />;
  }

  if (session.game_type === "TOWER_DEFENSE") {
    return <TowerDefenseGame session={session} />;
  }

  if (session.game_type === "BATTLE_ARENA") {
    return <BattleArenaGame session={session} />;
  }

  return <QuizGame session={session} />;
}

/** The classic "Viktorina" game — one question at a time, nothing revealed
 * about correctness until the end, score shown on the completion screen. */
function QuizGame({ session }: { session: GameSession }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});

  const questionsQuery = useQuery({
    queryKey: ["game", session.id, "questions"],
    queryFn: async () => (await api.get<GameQuestion[]>(`/games/${session.id}/questions/`)).data,
    enabled: session.status === "ACTIVE",
    retry: false,
  });

  const submitMutation = useMutation({
    mutationFn: async (finalAnswers: Record<number, number>) =>
      (
        await api.post<GameSession>(`/games/${session.id}/submit/`, {
          answers: Object.entries(finalAnswers).map(([question_index, selected_index]) => ({
            question_index: Number(question_index),
            selected_index,
          })),
        })
      ).data,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      queryClient.setQueryData(["game", session.id], result);
    },
    retry: 2,
  });

  const finished = submitMutation.data ?? (session.status === "COMPLETED" ? session : null);
  if (finished) return <QuizResult session={finished} />;

  const total = questionsQuery.data?.length ?? 0;

  return (
    <div className="mx-auto max-w-xl space-y-4">
      <GameHeaderBar title={`${session.subject_name} · ${session.game_type_display}`} totalXp={user?.total_xp ?? 0} />

      <div className="flex items-center justify-between text-xs font-medium text-slate-500 dark:text-slate-400">
        <span>
          Savol {Math.min(questionIndex + 1, total || 1)}/{total || "…"}
        </span>
      </div>
      <GameStepProgress index={questionIndex} total={total || 1} />

      {questionsQuery.isLoading && <LoadingState label="O'yin tayyorlanmoqda..." />}
      {questionsQuery.isError && isNoQuestionsError(questionsQuery.error) && (
        <EmptyState title={NO_QUESTIONS_TITLE} description={NO_QUESTIONS_HINT} />
      )}
      {questionsQuery.isError && !isNoQuestionsError(questionsQuery.error) && (
        <div className="space-y-3">
          <GameInlineError>Savollar hozircha tayyor emas. Birozdan so'ng qayta urinib ko'ring.</GameInlineError>
          <PrimaryButton onClick={() => questionsQuery.refetch()}>Qayta urinish</PrimaryButton>
        </div>
      )}

      {submitMutation.isError && (
        <div className="space-y-3">
          <GameInlineError>Natijalar saqlanmadi. Internetni tekshirib qayta urinib ko'ring.</GameInlineError>
          <PrimaryButton onClick={() => submitMutation.mutate(answers)}>Qayta yuborish</PrimaryButton>
        </div>
      )}

      {questionsQuery.data?.[questionIndex] && (
        <GameQuestionCard>
          <p className="text-base font-semibold text-slate-900 dark:text-slate-50">
            {questionsQuery.data[questionIndex].text}
          </p>
          <div className="mt-4 space-y-2.5">
            {questionsQuery.data[questionIndex].options.map((option, optionIndex) => (
              <GameOptionButton
                key={option}
                index={optionIndex}
                text={option}
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
              />
            ))}
          </div>
        </GameQuestionCard>
      )}
      {submitMutation.isPending && <LoadingState label="Natija hisoblanmoqda..." />}
    </div>
  );
}

function QuizResult({ session }: { session: GameSession }) {
  const score = session.score_percent ?? 0;
  const won = score >= 50;

  return (
    <GameResultScreen
      remedialSessionId={session?.remedial_session_id}
      tone={won ? "win" : "lose"}
      title={won ? "Zo'r natija!" : "Yana urinib ko'ring!"}
      subtitle={`Natija: ${score.toFixed(0)}%`}
      stats={[
        { label: "Natija", value: `${score.toFixed(0)}%` },
        {
          label: "Olingan XP",
          value: session.xp_awarded ? <AnimatedNumber value={session.xp_awarded} prefix="+" /> : "0",
          tone: "amber",
        },
      ]}
    />
  );
}
