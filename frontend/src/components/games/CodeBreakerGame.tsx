import { Clock, KeyRound, Layers, Lock, LockOpen, Target, X, Check, Zap } from "lucide-react";
import { useState } from "react";

import { useAuth } from "../../lib/auth";
import type { GameReviewItem, GameSession } from "../../types";
import {
  AnimatedNumber,
  formatDuration,
  GameHeaderBar,
  GameHudStat,
  GameInlineError,
  GameResultScreen,
  GameStartActions,
  GameStartStat,
  GameStepProgress,
} from "./GameUI";
import { LiveQuestionSection } from "./LiveQuestionSection";
import { SecurityTerminal } from "./SecurityTerminal";
import { playedSeconds, useLiveGame } from "./useLiveGame";

const SECONDS_PER_QUESTION_ESTIMATE = 30;
// Only a fallback for the type — the server always sends Kodni buzish's threshold.
const DEFAULT_UNLOCK_PERCENT = 70;

/** Kodni buzish (Code Breaker) — every correct answer decrypts one segment of
 * a per-session secret code; 70% opens the lock. The answer loop lives in
 * `useLiveGame`: each answer is locked in server-side before the key (and the
 * earned segment) comes back, and the full code is only ever sent by the
 * server after an unlocked finish. */
export function CodeBreakerGame({ session }: { session: GameSession }) {
  const { user } = useAuth();
  const total = session.question_count;
  const unlockPercent = session.unlock_percent ?? DEFAULT_UNLOCK_PERCENT;
  const [code, setCode] = useState<(string | null)[]>(
    session.revealed_code.length > 0 ? session.revealed_code : Array<string | null>(total).fill(null),
  );
  const [newSegmentIndex, setNewSegmentIndex] = useState<number | null>(null);
  const [alertKey, setAlertKey] = useState(0);

  const game = useLiveGame(session, {
    advanceMs: 1600,
    onAnswered: (result, index) => {
      if (result.correct && result.code_segment) {
        const segment = result.code_segment;
        setCode((prev) => prev.map((c, i) => (i === index ? segment : c)));
        setNewSegmentIndex(index);
      } else {
        setNewSegmentIndex(null);
        setAlertKey((k) => k + 1);
      }
    },
  });
  const { feedback, submitMutation } = game;

  if (game.phase === "start") {
    return (
      <StartScreen
        session={session}
        loading={game.questionsQuery.isLoading}
        error={game.questionsQuery.isError}
        unavailable={game.questionsUnavailable}
        resuming={session.answered_count > 0}
        onStart={game.start}
      />
    );
  }

  if (game.phase === "finished") {
    if (!game.finalSession) {
      return (
        <div className="mx-auto max-w-lg space-y-4">
          <SecurityTerminal
            code={code}
            correctCount={game.correctCount}
            answeredCount={total}
            total={total}
            unlockPercent={unlockPercent}
          />
          {submitMutation.isError ? (
            <div className="space-y-3">
              <GameInlineError>Natijalar saqlanmadi — internet aloqasi uzilgan bo'lishi mumkin.</GameInlineError>
              <button
                onClick={() => submitMutation.mutate()}
                className="w-full rounded-xl bg-brand-600 py-3 text-sm font-bold text-white hover:bg-brand-700"
              >
                Qayta yuborish
              </button>
            </div>
          ) : (
            <p className="text-center font-mono text-xs tracking-widest text-slate-500">VERIFYING ACCESS…</p>
          )}
        </div>
      );
    }
    return <CodeResult session={game.finalSession} elapsed={game.elapsed} onPlayAgain={game.playAgain} />;
  }

  const answered = game.answered;
  const scorePercent = answered > 0 ? Math.round((game.correctCount / answered) * 100) : 0;

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <GameHeaderBar title={`Code Breaker · ${session.subject_name}`} totalXp={user?.total_xp ?? 0} />

      <div className="grid grid-cols-4 gap-2 text-center">
        <GameHudStat icon={Layers} label="Savol" value={`${Math.min(game.questionIndex + 1, total)}/${total}`} />
        <GameHudStat icon={Target} label="Natija" value={`${scorePercent}%`} tone="emerald" />
        <GameHudStat icon={Zap} label="XP" value={`+${game.xpEarned}`} tone="amber" />
        <GameHudStat icon={Clock} label="Vaqt" value={formatDuration(game.elapsed)} />
      </div>
      <GameStepProgress index={answered} total={total} />

      <SecurityTerminal
        code={code}
        correctCount={game.correctCount}
        answeredCount={answered}
        total={total}
        unlockPercent={unlockPercent}
        newSegmentIndex={feedback ? newSegmentIndex : null}
        alertKey={alertKey}
      />

      <LiveQuestionSection
        game={game}
        label={`${game.questionIndex + 1}-segment`}
        wrongTitle="Noto'g'ri — segment yopiq qoldi"
        successDetail={
          <>
            Segment ochildi
            <span className="rounded-md border border-brand-400/60 bg-brand-500/15 px-1.5 py-0.5 font-mono text-sm font-bold text-brand-700 dark:text-sky-200">
              {feedback?.result.code_segment}
            </span>
          </>
        }
      />
    </div>
  );
}

function CodeResult({
  session,
  elapsed,
  onPlayAgain,
}: {
  session: GameSession;
  elapsed: number;
  onPlayAgain: () => void;
}) {
  const total = session.question_count;
  const correct = session.correct_count;
  const accuracy = Math.round(session.score_percent ?? 0);
  const unlocked = session.goal_reached;
  const unlockPercent = session.unlock_percent ?? DEFAULT_UNLOCK_PERCENT;
  const seconds = playedSeconds(elapsed, session);
  const mistakes = (session.review ?? []).filter((item) => item.selected_index !== item.correct_index);

  return (
    <GameResultScreen
      remedialSessionId={session?.remedial_session_id}
      tone={unlocked ? "win" : "lose"}
      icon={unlocked ? LockOpen : Lock}
      title={unlocked ? "CODE UNLOCKED" : "CODE LOCKED"}
      subtitle={
        unlocked
          ? "Ajoyib! Bilimingiz bilan himoya tizimini buzdingiz."
          : `Kodni ochish uchun ${unlockPercent}% kerak edi — siz ${accuracy}% to'pladingiz.`
      }
      stats={[
        { label: "To'g'ri javoblar", value: `${correct}/${total}` },
        { label: "Aniqlik", value: `${accuracy}%` },
        {
          label: "Olingan XP",
          value: session.xp_awarded ? <AnimatedNumber value={session.xp_awarded} prefix="+" /> : "0",
          tone: "amber",
        },
        { label: "Vaqt", value: formatDuration(seconds) },
      ]}
      onPrimary={onPlayAgain}
      primaryLabel={unlocked ? "Qayta o'ynash" : "Qayta urinib ko'rish"}
      secondaryLabel="O'yinlarga qaytish"
    >
      <SecurityTerminal
        code={session.revealed_code}
        correctCount={correct}
        answeredCount={total}
        total={total}
        unlockPercent={unlockPercent}
        state={unlocked ? "unlocked" : "locked"}
      />
      {!unlocked && mistakes.length > 0 && <MistakeReview items={mistakes} />}
    </GameResultScreen>
  );
}

function MistakeReview({ items }: { items: GameReviewItem[] }) {
  return (
    <div className="space-y-2 text-left">
      <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Xato javoblar</h2>
      {items.map((item) => (
        <div
          key={item.text}
          className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
        >
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">{item.text}</p>
          <div className="mt-2 space-y-1 text-sm">
            <p className="flex items-start gap-1.5 text-red-600 dark:text-red-400">
              <X size={14} className="mt-0.5 shrink-0" />
              {item.selected_index >= 0 ? item.options[item.selected_index] : "Javob berilmagan"}
            </p>
            <p className="flex items-start gap-1.5 text-emerald-600 dark:text-emerald-400">
              <Check size={14} className="mt-0.5 shrink-0" />
              {item.options[item.correct_index]}
            </p>
          </div>
          {item.explanation && <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{item.explanation}</p>}
        </div>
      ))}
    </div>
  );
}

function StartScreen({
  session,
  loading,
  error,
  unavailable,
  resuming,
  onStart,
}: {
  session: GameSession;
  loading: boolean;
  error: boolean;
  unavailable: boolean;
  resuming: boolean;
  onStart: () => void;
}) {
  const total = session.question_count;
  const minutes = Math.max(1, Math.round((total * SECONDS_PER_QUESTION_ESTIMATE) / 60));
  const unlockPercent = session.unlock_percent ?? DEFAULT_UNLOCK_PERCENT;
  const needed = Math.ceil((total * unlockPercent) / 100);
  const preview = session.revealed_code.length > 0 ? session.revealed_code : Array<string | null>(total).fill(null);

  return (
    <div className="mx-auto max-w-2xl space-y-5 text-center">
      <div className="rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 px-6 pt-8 sm:px-8">
        <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-brand-400/40 bg-brand-500/10 text-sky-300 shadow-[0_0_24px_rgba(59,130,246,0.35)]">
          <KeyRound size={22} />
        </span>
        <h1 className="mt-3 font-mono text-2xl font-black tracking-[0.2em] text-white sm:text-3xl">CODE BREAKER</h1>
        <p className="mt-1 text-sm text-slate-400">
          {session.subject_name} savollariga javob berib, maxfiy kodni buzing.
        </p>
        <div className="mt-6 pb-6 text-left">
          <SecurityTerminal
            code={preview}
            correctCount={session.correct_count}
            answeredCount={session.answered_count}
            total={total}
            unlockPercent={unlockPercent}
          />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <GameStartStat label="Savollar" value={`${total} ta`} />
        <GameStartStat label="Maksimal XP" value={`${session.max_xp} XP`} tone="amber" />
        <GameStartStat label="Taxminiy vaqt" value={`~${minutes} daq`} />
      </div>

      <p className="text-sm text-slate-500 dark:text-slate-400">
        Har bir to'g'ri javob kodning bitta segmentini ochadi. Kamida {needed}/{total} ({unlockPercent}%) to'g'ri javob
        bersangiz — kod to'liq ochiladi.
      </p>

      <GameStartActions
        loading={loading}
        error={error}
        unavailable={unavailable}
        resuming={resuming}
        onStart={onStart}
        label="Buzishni boshlash"
      />
    </div>
  );
}
