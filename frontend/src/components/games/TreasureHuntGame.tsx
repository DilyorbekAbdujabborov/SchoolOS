import { Clock, Compass, Gem, Layers, MapPin, Sparkles, Zap } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "../../lib/auth";
import type { GameSession } from "../../types";
import {
  AnimatedNumber,
  formatDuration,
  GameHeaderBar,
  GameHudStat,
  GameInlineError,
  GameResultScreen,
  GameStartActions,
  GameStartStat,
} from "./GameUI";
import { LiveQuestionSection } from "./LiveQuestionSection";
import { MAP_LOCATIONS, TreasureChest, TreasureMap } from "./TreasureMap";
import { playedSeconds, useLiveGame } from "./useLiveGame";

const SECONDS_PER_QUESTION_ESTIMATE = 30;
// Only a fallback for the type — the server always sends Xazina ovi's threshold.
const DEFAULT_UNLOCK_PERCENT = 80;
// Explorer walk (~0.95s) + a beat to take in the newly discovered location.
const ADVANCE_MS = 2300;
// How long the open chest stays on the map before the result screen.
const FINALE_MS = 3400;

function locationName(stop: number): string {
  return stop === 0 ? "Lager" : MAP_LOCATIONS[stop - 1].name;
}

/** Xazina ovi (Treasure Hunt) — each correct answer walks the explorer one
 * location further along the map; reaching the threshold (80%) opens the
 * treasure at the end. The answer loop and scoring live in `useLiveGame`
 * (answers locked in server-side, XP from the server); this component is the
 * map, the journey HUD and the treasure finale. */
export function TreasureHuntGame({ session }: { session: GameSession }) {
  const { user } = useAuth();
  const total = session.question_count;
  const unlockPercent = session.unlock_percent ?? DEFAULT_UNLOCK_PERCENT;
  const needed = Math.ceil((total * unlockPercent) / 100);

  const [discovery, setDiscovery] = useState<{
    stop: number;
    xp: number;
    key: number;
  } | null>(null);
  const [alertKey, setAlertKey] = useState(0);
  // Revisiting an already-finished game skips straight to its result.
  const [finaleDone, setFinaleDone] = useState(session.status === "COMPLETED");
  const [chestOpen, setChestOpen] = useState(false);

  const game = useLiveGame(session, {
    advanceMs: ADVANCE_MS,
    onAnswered: (result) => {
      if (!result.correct) {
        setDiscovery(null);
        setAlertKey((k) => k + 1);
      }
    },
  });
  const { feedback, submitMutation, finalSession } = game;
  const explored = game.correctCount;
  const reachedTreasure = Boolean(finalSession?.goal_reached);

  // Hold the open chest on screen for a moment, then show the result.
  useEffect(() => {
    if (!chestOpen) return;
    const t = setTimeout(() => setFinaleDone(true), FINALE_MS);
    return () => clearTimeout(t);
  }, [chestOpen]);

  if (game.phase === "start") {
    return (
      <StartScreen
        session={session}
        needed={needed}
        loading={game.questionsQuery.isLoading}
        error={game.questionsQuery.isError}
        resuming={session.answered_count > 0}
        onStart={game.start}
      />
    );
  }

  if (game.phase === "finished" && finalSession && (finaleDone || !reachedTreasure)) {
    return <HuntResult session={finalSession} elapsed={game.elapsed} onPlayAgain={game.playAgain} />;
  }

  const finishing = game.phase === "finished";
  const atStop = Math.min(explored, MAP_LOCATIONS.length);
  const remaining = total - game.answered;
  const stillNeeded = Math.max(0, needed - explored);

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <GameHeaderBar title={`Treasure Hunt · ${session.subject_name}`} totalXp={user?.total_xp ?? 0} />

      <div className="grid grid-cols-3 gap-2 text-center">
        <GameHudStat icon={Layers} label="Savol" value={`${Math.min(game.questionIndex + 1, total)}/${total}`} />
        <GameHudStat icon={Zap} label="XP" value={`+${game.xpEarned}`} tone="amber" />
        <GameHudStat icon={Clock} label="Vaqt" value={formatDuration(game.elapsed)} />
      </div>

      <JourneyProgress
        explored={explored}
        total={total}
        needed={needed}
        hint={
          finishing
            ? reachedTreasure
              ? "Xazina yo'li ochildi!"
              : "Sayohat yakunlanmoqda…"
            : stillNeeded === 0
              ? "Xazinaga yo'l ochiq — sayohatni yakunlang!"
              : stillNeeded > remaining
                ? "Bu safar xazinaga yetib bo'lmaydi, lekin har bir manzil hisobga olinadi."
                : `Xazinaga yetish uchun yana ${stillNeeded} ta to'g'ri javob kerak`
        }
      />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-start">
        <div key={alertKey} className={alertKey > 0 && !finishing ? "animate-alert-flash rounded-2xl" : "rounded-2xl"}>
          <TreasureMap
            explored={explored}
            reachTreasure={finishing && reachedTreasure}
            onArrive={(stop) => {
              if (stop > MAP_LOCATIONS.length) {
                setChestOpen(true);
              } else if (stop > 0) {
                setDiscovery((prev) => ({
                  stop,
                  xp: feedback?.xpGained ?? 0,
                  key: (prev?.key ?? 0) + 1,
                }));
              }
            }}
          >
            <span className="absolute left-3 top-3 flex items-center gap-1.5 rounded-lg border border-white/10 bg-slate-950/60 px-2.5 py-1.5 text-xs font-semibold text-sky-100 backdrop-blur">
              <MapPin size={13} className="text-sky-400" />
              {locationName(atStop)}
            </span>

            {discovery && feedback?.result.correct && !finishing && (
              <>
                <div
                  key={`toast-${discovery.key}`}
                  className="absolute left-1/2 top-3 -translate-x-1/2 animate-pop-in rounded-xl border border-sky-400/40 bg-slate-950/70 px-4 py-2 text-center shadow-[0_0_24px_rgba(56,189,248,0.3)] backdrop-blur"
                >
                  <p className="font-mono text-[10px] font-bold uppercase tracking-[0.25em] text-sky-300">
                    Manzil kashf etildi
                  </p>
                  <p className="text-sm font-bold text-white">{locationName(discovery.stop)}</p>
                </div>
                <div key={`xp-${discovery.key}`} className="absolute right-3 top-3 animate-float-up text-right">
                  <p className="text-lg font-black text-amber-400">+{discovery.xp} XP</p>
                </div>
              </>
            )}

            {finishing && !finalSession && (
              <div className="absolute inset-0 flex animate-fade-in items-center justify-center bg-slate-950/50 backdrop-blur-[2px]">
                {submitMutation.isError ? (
                  <div className="mx-4 max-w-sm space-y-3">
                    <GameInlineError>Natijalar saqlanmadi — internet aloqasi uzilgan bo'lishi mumkin.</GameInlineError>
                    <button
                      onClick={() => submitMutation.mutate()}
                      className="w-full rounded-xl bg-brand-600 py-3 text-sm font-bold text-white hover:bg-brand-700"
                    >
                      Qayta yuborish
                    </button>
                  </div>
                ) : (
                  <p className="font-mono text-xs tracking-[0.3em] text-sky-200">SAYOHAT YAKUNLANMOQDA…</p>
                )}
              </div>
            )}

            {chestOpen && <TreasureMoment />}
          </TreasureMap>
        </div>

        {!finishing && (
          <div className="space-y-3">
            <LiveQuestionSection
              game={game}
              stacked
              label={`Challenge ${String(game.questionIndex + 1).padStart(2, "0")}`}
              wrongTitle="Noto'g'ri — yo'l hozircha yopiq"
              successDetail={
                <span className="flex items-center gap-1.5 truncate">
                  <Compass size={13} />
                  {explored >= MAP_LOCATIONS.length
                    ? "Oltin darvozaga yetdingiz"
                    : `Keyingi manzil: ${locationName(atStop)}`}
                </span>
              }
            />
          </div>
        )}
      </div>
    </div>
  );
}

/** Journey progress — ten location ticks, the treasure threshold, and the gem at the end. */
function JourneyProgress({
  explored,
  total,
  needed,
  hint,
}: {
  explored: number;
  total: number;
  needed: number;
  hint: string;
}) {
  const percent = total > 0 ? (Math.min(explored, total) / total) * 100 : 0;
  const thresholdReached = explored >= needed;
  return (
    <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between text-xs font-semibold">
        <span className="uppercase tracking-wider text-slate-500 dark:text-slate-400">Sayohat</span>
        <span className="text-slate-900 dark:text-slate-50">
          {Math.min(explored, total)}/{total} manzil
        </span>
      </div>
      <div className="mt-2 flex items-center gap-3">
        <div className="relative h-2 flex-1 rounded-full bg-slate-100 dark:bg-slate-800">
          <div
            className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-brand-500 to-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.5)] transition-[width] duration-1000 ease-out"
            style={{ width: `${percent}%` }}
          />
          {Array.from({ length: total - 1 }, (_, i) => (
            <span
              key={i}
              className="absolute top-1/2 h-1 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/60 dark:bg-slate-950/70"
              style={{ left: `${((i + 1) / total) * 100}%` }}
            />
          ))}
          <span
            className="absolute -top-1 h-4 w-0.5 -translate-x-1/2 rounded-full bg-amber-400"
            style={{ left: `${(needed / total) * 100}%` }}
            title="Xazina chegarasi"
          />
        </div>
        <span
          className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg border transition-colors ${
            thresholdReached
              ? "border-amber-400/60 bg-amber-400/15 text-amber-500 shadow-[0_0_14px_rgba(251,191,36,0.45)]"
              : "border-slate-200 text-slate-400 dark:border-slate-700 dark:text-slate-500"
          }`}
        >
          <Gem size={14} />
        </span>
      </div>
      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{hint}</p>
    </div>
  );
}

function TreasureMoment() {
  return (
    <div className="absolute inset-0 flex animate-fade-in flex-col items-center justify-center bg-gradient-to-t from-slate-950/90 via-slate-950/60 to-amber-500/10">
      <TreasureChest open className="h-36 w-auto drop-shadow-[0_0_40px_rgba(251,191,36,0.45)] sm:h-48" />
      <p className="mt-2 animate-pop-in font-mono text-xs font-bold uppercase tracking-[0.35em] text-amber-300 [animation-delay:0.9s]">
        Treasure unlocked
      </p>
      <p className="mt-1 animate-pop-in text-2xl font-black tracking-wide text-white [animation-delay:1.1s] sm:text-3xl">
        Xazina topildi!
      </p>
    </div>
  );
}

function HuntResult({
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
  const found = session.goal_reached;
  const unlockPercent = session.unlock_percent ?? DEFAULT_UNLOCK_PERCENT;
  const needed = Math.ceil((total * unlockPercent) / 100);
  const explored = Math.min(correct, MAP_LOCATIONS.length);

  const stats = [
    { label: "To'g'ri javoblar", value: `${correct}/${total}` },
    { label: "Aniqlik", value: `${accuracy}%` },
    {
      label: "Olingan XP",
      value: session.xp_awarded ? <AnimatedNumber value={session.xp_awarded} prefix="+" /> : "0",
      tone: "amber" as const,
    },
    { label: "Vaqt", value: formatDuration(playedSeconds(elapsed, session)) },
  ];

  if (found) {
    return (
      <GameResultScreen
        tone="win"
        icon={Gem}
        title="TREASURE FOUND"
        subtitle={`Tabriklaymiz! ${explored} ta manzilni kashf etib, xazinaga yetib keldingiz.`}
        stats={stats}
        onPrimary={onPlayAgain}
        primaryLabel="Qayta o'ynash"
        secondaryLabel="O'yinlarga qaytish"
      >
        <div className="relative overflow-hidden rounded-2xl border border-amber-400/20 bg-gradient-to-b from-slate-900 to-slate-950 py-4">
          <TreasureChest open className="mx-auto h-40 w-auto drop-shadow-[0_0_36px_rgba(251,191,36,0.4)]" />
          <p className="mt-1 flex items-center justify-center gap-1.5 font-mono text-[11px] font-bold uppercase tracking-[0.3em] text-amber-300">
            <Sparkles size={12} /> Treasure unlocked
          </p>
        </div>
      </GameResultScreen>
    );
  }

  return (
    <GameResultScreen
      tone="neutral"
      icon={Compass}
      title="JOURNEY COMPLETE"
      subtitle={`Siz ${explored}/${total} manzilni kashf etdingiz. Xazinaga yetish uchun ${needed} ta kerak — keyingi safar albatta yetasiz!`}
      stats={[...stats, { label: "Ochilgan manzillar", value: `${explored}/${total}` }]}
      onPrimary={onPlayAgain}
      primaryLabel="Qayta urinish"
      secondaryLabel="O'yinlarga qaytish"
    >
      <TreasureMap explored={explored} overview forceWide />
    </GameResultScreen>
  );
}

function StartScreen({
  session,
  needed,
  loading,
  error,
  resuming,
  onStart,
}: {
  session: GameSession;
  needed: number;
  loading: boolean;
  error: boolean;
  resuming: boolean;
  onStart: () => void;
}) {
  const total = session.question_count;
  const minutes = Math.max(1, Math.round((total * SECONDS_PER_QUESTION_ESTIMATE) / 60));

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <div className="text-center">
        <p className="font-mono text-[11px] font-bold uppercase tracking-[0.35em] text-brand-600 dark:text-sky-300/90">
          {session.subject_name} · Sayohat
        </p>
        <h1 className="mt-2 text-3xl font-black tracking-[0.18em] text-slate-900 dark:text-white dark:drop-shadow-[0_0_24px_rgba(56,189,248,0.45)] sm:text-4xl">
          TREASURE HUNT
        </h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-slate-500 dark:text-slate-300">
          Har bir to'g'ri javob sizni xaritada bir manzil oldinga olib boradi. Oltin darvozadan o'tib, xazinani toping.
        </p>
      </div>

      <TreasureMap explored={session.correct_count} overview />

      <div className="mx-auto max-w-lg space-y-4 text-center">
        <div className="grid grid-cols-3 gap-2">
          <GameStartStat label="Savollar" value={`${total} ta`} />
          <GameStartStat label="Maksimal XP" value={`${session.max_xp} XP`} tone="amber" />
          <GameStartStat label="Taxminiy vaqt" value={`~${minutes} daq`} />
        </div>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Xazinaga yetish uchun kamida {needed}/{total} ta to'g'ri javob kerak.
        </p>
        <GameStartActions
          loading={loading}
          error={error}
          resuming={resuming}
          onStart={onStart}
          label="Sayohatni boshlash"
        />
      </div>
    </div>
  );
}
