import { Building2, Clock, Layers, Zap } from "lucide-react";
import { useState } from "react";

import { useAuth } from "../../lib/auth";
import type { GameSession } from "../../types";
import {
  AnimatedNumber,
  formatDuration,
  GameHeaderBar,
  GameHudStat,
  GameResultScreen,
  GameStartActions,
  GameStartStat,
  GameStepProgress,
} from "./GameUI";
import { LiveQuestionSection } from "./LiveQuestionSection";
import { TowerScene } from "./TowerScene";
import { playedSeconds, useLiveGame } from "./useLiveGame";

const SECONDS_PER_QUESTION_ESTIMATE = 30;

/** Minora qurish — every correct answer adds a floor. The answer loop,
 * scoring and resume live in `useLiveGame`; this component is the tower. */
export function TowerBuilderGame({ session }: { session: GameSession }) {
  const { user } = useAuth();
  const [newFloorKey, setNewFloorKey] = useState(0);
  const game = useLiveGame(session, {
    onAnswered: (result) => {
      if (result.correct) setNewFloorKey((k) => k + 1);
    },
  });
  const { total, feedback, submitMutation } = game;
  const floors = game.correctCount;

  if (game.phase === "start") {
    return (
      <StartScreen
        session={session}
        loading={game.questionsQuery.isLoading}
        error={game.questionsQuery.isError}
        resuming={session.answered_count > 0}
        onStart={game.start}
      />
    );
  }

  if (game.phase === "finished") {
    const finalSession = game.finalSession;
    const correct = finalSession?.correct_count ?? floors;
    const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;
    const xpAwarded = finalSession?.xp_awarded ?? game.xpEarned;

    return (
      <GameResultScreen
        tone={accuracy >= 50 ? "win" : "lose"}
        icon={Building2}
        title="Minora qurildi!"
        subtitle={`Minora balandligi: ${correct} qavat`}
        stats={[
          { label: "To'g'ri javoblar", value: `${correct}/${total}` },
          { label: "Aniqlik", value: `${accuracy}%` },
          {
            label: "Olingan XP",
            value: submitMutation.isPending ? "…" : submitMutation.isError ? "—" : <AnimatedNumber value={xpAwarded} prefix="+" />,
            tone: "amber",
          },
          { label: "Vaqt", value: formatDuration(playedSeconds(game.elapsed, finalSession)) },
        ]}
        errorMessage={
          submitMutation.isError ? "Natijalar saqlanmadi — internet aloqasi uzilgan bo'lishi mumkin." : undefined
        }
        onRetry={() => submitMutation.mutate()}
        onPrimary={game.playAgain}
        primaryLabel="Qayta o'ynash"
        secondaryLabel="O'yinlar sahifasiga qaytish"
      >
        <TowerArena floors={correct} maxFloors={total} complete />
      </GameResultScreen>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <GameHeaderBar title={`${session.subject_name} · ${session.game_type_display}`} totalXp={user?.total_xp ?? 0} />

      <div className="grid grid-cols-4 gap-2 text-center">
        <GameHudStat icon={Layers} label="Savol" value={`${Math.min(game.questionIndex + 1, total)}/${total}`} />
        <GameHudStat icon={Zap} label="XP" value={`+${game.xpEarned}`} tone="amber" />
        <GameHudStat icon={Building2} label="Qavat" value={`${floors}`} tone="emerald" />
        <GameHudStat icon={Clock} label="Vaqt" value={formatDuration(game.elapsed)} />
      </div>
      <GameStepProgress index={game.answered} total={total} />

      <TowerArena
        floors={floors}
        maxFloors={total}
        newFloorKey={newFloorKey}
        celebration={feedback?.result.correct ? { key: newFloorKey, xp: feedback.xpGained } : undefined}
      />

      <LiveQuestionSection
        game={game}
        successDetail={<span className="uppercase tracking-wide">Yangi qavat qurildi</span>}
      />
    </div>
  );
}

function TowerArena({
  floors,
  maxFloors,
  newFloorKey,
  complete,
  celebration,
}: {
  floors: number;
  maxFloors: number;
  newFloorKey?: number;
  complete?: boolean;
  celebration?: { key: number; xp: number };
}) {
  return (
    <div className="relative h-60 overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 px-3 pt-3 sm:h-72">
      <TowerScene floors={floors} maxFloors={maxFloors} newFloorKey={newFloorKey} complete={complete} />
      <span className="absolute left-3 top-3 rounded-lg bg-white/10 px-2 py-1 text-xs font-semibold text-white/90 backdrop-blur">
        {floors}/{maxFloors} qavat
      </span>
      {celebration && (
        <div key={celebration.key} className="animate-float-up absolute right-3 top-3 text-right">
          <p className="text-lg font-black text-amber-400">+{celebration.xp} XP</p>
          <p className="text-[10px] font-bold uppercase tracking-widest text-sky-200">Yangi qavat</p>
        </div>
      )}
    </div>
  );
}

function StartScreen({
  session,
  loading,
  error,
  resuming,
  onStart,
}: {
  session: GameSession;
  loading: boolean;
  error: boolean;
  resuming: boolean;
  onStart: () => void;
}) {
  const minutes = Math.max(1, Math.round((session.question_count * SECONDS_PER_QUESTION_ESTIMATE) / 60));
  return (
    <div className="mx-auto max-w-lg space-y-5 text-center">
      <div className="overflow-hidden rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 px-8 pt-8">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-sky-300/80">Tower Builder</p>
        <h1 className="mt-2 text-2xl font-bold text-white">Minora qurish</h1>
        <p className="mt-1 text-sm text-slate-400">Biliming bilan minorangni qur.</p>
        <div className="mt-4 h-40">
          <TowerScene floors={3} maxFloors={session.question_count} />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <GameStartStat label="Savollar" value={`${session.question_count} ta`} />
        <GameStartStat label="Maksimal XP" value={`${session.max_xp} XP`} tone="amber" />
        <GameStartStat label="Taxminiy vaqt" value={`~${minutes} daq`} />
      </div>

      <p className="text-sm text-slate-500 dark:text-slate-400">
        Har bir to'g'ri javob minoraga yangi qavat qo'shadi. Noto'g'ri javobda to'g'ri variant va qisqa izoh
        ko'rsatiladi.
      </p>

      <GameStartActions loading={loading} error={error} resuming={resuming} onStart={onStart} />
    </div>
  );
}
