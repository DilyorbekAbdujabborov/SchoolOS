import { Check, X, Zap, type LucideIcon, Trophy } from "lucide-react";
import { useEffect, useRef, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { useCountUp } from "../../lib/useCountUp";

/** Shared visual language for every gameplay screen (Arqon tortish, Viktorina,
 * Duel) — one HUD, one option-button anatomy, one result screen — so a
 * student can jump between game types and immediately recognize the same
 * product, only the game-specific center stage (rope, question set, etc.)
 * differs. */

const LETTERS = ["A", "B", "C", "D", "E", "F"];

export function AnimatedNumber({ value, prefix = "" }: { value: number; prefix?: string }) {
  const animated = useCountUp(value, { startFrom: 0, durationMs: 1100 });
  return (
    <>
      {prefix}
      {animated}
    </>
  );
}

export function formatDuration(totalSeconds: number): string {
  const s = Math.max(0, Math.floor(totalSeconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** One fact on a game's start screen — question count, max XP, estimated time. */
export function GameStartStat({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "amber";
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p
        className={`mt-0.5 text-sm font-bold ${
          tone === "amber" ? "text-amber-600 dark:text-amber-400" : "text-slate-900 dark:text-slate-50"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

/** The subject/game-type line + running XP total shown above every game. */
export function GameHeaderBar({ title, totalXp }: { title: string; totalXp: number }) {
  return (
    <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
      <span className="font-semibold text-slate-800 dark:text-slate-100">{title}</span>
      <span className="flex items-center gap-1 font-medium text-brand-600 dark:text-brand-400">
        <Zap size={14} /> Jami {totalXp} XP
      </span>
    </div>
  );
}

export function GameHudStat({
  icon: Icon,
  label,
  value,
  tone = "brand",
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  tone?: "brand" | "emerald" | "amber";
}) {
  const toneClass = {
    brand: "text-brand-600 dark:text-brand-400",
    emerald: "text-emerald-600 dark:text-emerald-400",
    amber: "text-amber-600 dark:text-amber-400",
  }[tone];
  return (
    <div className="rounded-xl border border-slate-200 bg-white py-2 dark:border-slate-800 dark:bg-slate-900">
      <p className={`flex items-center justify-center gap-1 text-xs font-medium ${toneClass}`}>
        <Icon size={12} /> {label}
      </p>
      <p className="mt-0.5 text-sm font-bold text-slate-900 dark:text-slate-50">{value}</p>
    </div>
  );
}

/** A slim "question N of total" fill bar — the step-progress counterpart to
 * Arqon tortish's per-question countdown (`TimerBar`), for games that pace
 * by question count rather than a clock. */
export function GameStepProgress({ index, total }: { index: number; total: number }) {
  const percent = total > 0 ? Math.min(100, Math.max(0, (index / total) * 100)) : 0;
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
      <div
        className="h-full rounded-full bg-brand-500 transition-[width] duration-500 ease-out"
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}

export type GameOptionState = "default" | "selected" | "correct" | "incorrect";

/** One answer choice — same lettered-badge anatomy everywhere. `state`
 * covers both the "which one did I pick" case (Duel, still editable) and
 * the "here's what just happened" case (Arqon tortish's instant feedback);
 * a game that never reveals correctness mid-round (Viktorina) simply never
 * passes "correct"/"incorrect". */
export function GameOptionButton({
  index,
  text,
  state = "default",
  disabled,
  onClick,
}: {
  index: number;
  text: string;
  state?: GameOptionState;
  disabled?: boolean;
  onClick?: () => void;
}) {
  const stateClass =
    state === "correct"
      ? "border-emerald-500 bg-emerald-50 dark:border-emerald-400 dark:bg-emerald-500/10"
      : state === "incorrect"
        ? "border-red-500 bg-red-50 dark:border-red-400 dark:bg-red-500/10"
        : state === "selected"
          ? "border-brand-500 bg-brand-50 dark:border-brand-400 dark:bg-brand-500/10"
          : "border-slate-200 hover:border-brand-400 hover:bg-brand-50/60 dark:border-slate-700 dark:hover:bg-brand-500/10";

  const badgeToneClass =
    state === "correct"
      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400"
      : state === "incorrect"
        ? "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400"
        : state === "selected"
          ? "bg-brand-100 text-brand-700 dark:bg-brand-500/15 dark:text-brand-400"
          : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400";

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex w-full items-center gap-3 rounded-xl border-2 px-4 py-3 text-left text-sm font-medium text-slate-700 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 focus-visible:ring-offset-white active:scale-[0.97] disabled:cursor-default dark:text-slate-200 dark:focus-visible:ring-offset-slate-900 ${stateClass}`}
    >
      <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold ${badgeToneClass}`}>
        {state === "correct" ? <Check size={14} /> : state === "incorrect" ? <X size={14} /> : LETTERS[index]}
      </span>
      {text}
    </button>
  );
}

/** A game's question card — same card, same question typography, everywhere. */
export function GameQuestionCard({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      {children}
    </div>
  );
}

export function GameInlineError({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-center dark:border-red-500/30 dark:bg-red-500/10">
      <p className="text-sm text-red-700 dark:text-red-300">{children}</p>
    </div>
  );
}

export type GameResultTone = "win" | "draw" | "lose" | "neutral";

const TONE_GRADIENT: Record<GameResultTone, string> = {
  win: "bg-gradient-to-br from-brand-500 to-brand-700",
  draw: "bg-gradient-to-br from-slate-500 to-slate-700",
  lose: "bg-gradient-to-br from-slate-700 to-slate-900",
  neutral: "bg-gradient-to-br from-slate-700 to-slate-900",
};

export interface GameResultStat {
  label: string;
  value: ReactNode;
  tone?: "default" | "amber";
}

/** The completion screen every game lands on — trophy, title, a small stat
 * grid, an optional submit-failed/retry banner, then "play again" + "back
 * to the list". Game-specific state (score vs. opponent, XP earned, correct
 * count) is passed in as `stats`; the shell stays identical. */
export function GameResultScreen({
  tone,
  icon: Icon = Trophy,
  title,
  subtitle,
  stats,
  errorMessage,
  onRetry,
  onPrimary,
  primaryLabel = "Yana o'ynash",
  secondaryTo = "/student/games",
  secondaryLabel = "O'yinlar ro'yxatiga qaytish",
  children,
}: {
  tone: GameResultTone;
  icon?: LucideIcon;
  title: string;
  subtitle: string;
  stats: GameResultStat[];
  errorMessage?: string;
  onRetry?: () => void;
  onPrimary?: () => void;
  primaryLabel?: string;
  secondaryTo?: string;
  secondaryLabel?: string;
  /** Optional game-specific showcase between the header and the stats (e.g. the finished tower). */
  children?: ReactNode;
}) {
  const gridClass =
    stats.length >= 5
      ? "grid-cols-2 sm:grid-cols-3"
      : stats.length === 4
      ? "grid-cols-2 sm:grid-cols-4"
      : stats.length === 3
        ? "grid-cols-3"
        : stats.length === 2
          ? "grid-cols-2"
          : "grid-cols-1";

  return (
    <div className="mx-auto max-w-lg space-y-5 text-center">
      <div className={`animate-pop-in rounded-2xl p-8 text-white ${TONE_GRADIENT[tone]}`}>
        <Icon className="mx-auto h-10 w-10" />
        <h1 className="mt-3 text-2xl font-bold">{title}</h1>
        <p className="mt-1 text-sm text-white/80">{subtitle}</p>
      </div>

      {children}

      {stats.length > 0 && (
        <div className={`grid gap-3 ${gridClass}`}>
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
            >
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{stat.label}</p>
              <p
                className={`mt-1 text-xl font-bold ${
                  stat.tone === "amber" ? "text-amber-600 dark:text-amber-400" : "text-slate-900 dark:text-slate-50"
                }`}
              >
                {stat.value}
              </p>
            </div>
          ))}
        </div>
      )}

      {errorMessage && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300">
          <p>{errorMessage}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 rounded-lg bg-red-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-red-700"
            >
              Qayta yuborish
            </button>
          )}
        </div>
      )}

      <div className="flex flex-col gap-2 sm:flex-row">
        {onPrimary && (
          <button
            onClick={onPrimary}
            className="flex-1 rounded-xl bg-brand-600 py-3 text-sm font-bold text-white transition-transform hover:bg-brand-700 active:scale-[0.98]"
          >
            {primaryLabel}
          </button>
        )}
        <Link
          to={secondaryTo}
          className="flex-1 rounded-xl border border-slate-200 py-3 text-sm font-bold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          {secondaryLabel}
        </Link>
      </div>
    </div>
  );
}

/** The after-answer banner for games that reveal the key mid-round (Minora
 * qurish, Kodni buzish, Xazina ovi). Correct: a one-line success strip with
 * the XP gained and a game-specific `successDetail` ("Yangi qavat", the
 * unlocked code segment…); it moves on by itself. Wrong: the correct option
 * and the question's explanation, and the student presses on when ready. */
export function GameAnswerFeedback({
  correct,
  xpGained,
  successDetail,
  wrongTitle = "Noto'g'ri",
  explanationLabel,
  correctAnswerText,
  explanation,
  isLast,
  onNext,
}: {
  correct: boolean;
  xpGained: number;
  successDetail?: ReactNode;
  wrongTitle?: string;
  /** Small heading above the explanation, e.g. "Nega?". */
  explanationLabel?: string;
  correctAnswerText?: string;
  explanation?: string;
  isLast: boolean;
  onNext: () => void;
}) {
  // Keyboard players can press Enter to continue — focus the button without
  // scrolling the page (that would push the game's HUD out of view).
  const nextRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (!correct) nextRef.current?.focus({ preventScroll: true });
  }, [correct]);

  if (correct) {
    return (
      <div className="animate-pop-in flex items-center justify-between gap-3 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 dark:border-emerald-500/30 dark:bg-emerald-500/10">
        <p className="flex items-center gap-2 text-sm font-bold text-emerald-700 dark:text-emerald-300">
          <Check size={16} /> To'g'ri!
        </p>
        {successDetail && (
          <div className="flex min-w-0 items-center gap-2 text-xs font-semibold text-emerald-700/80 dark:text-emerald-300/80">
            {successDetail}
          </div>
        )}
        <p className="shrink-0 text-sm font-bold text-amber-600 dark:text-amber-400">+{xpGained} XP</p>
      </div>
    );
  }

  return (
    <div className="animate-pop-in space-y-3 rounded-2xl border border-red-200 bg-red-50 p-4 dark:border-red-500/30 dark:bg-red-500/10">
      <p className="flex items-center gap-2 text-sm font-bold text-red-700 dark:text-red-300">
        <X size={16} /> {wrongTitle}
      </p>
      {correctAnswerText !== undefined && (
        <p className="text-sm text-slate-700 dark:text-slate-200">
          To'g'ri javob: <span className="font-semibold text-slate-900 dark:text-slate-50">{correctAnswerText}</span>
        </p>
      )}
      {explanation && (
        <div>
          {explanationLabel && (
            <p className="text-[11px] font-bold uppercase tracking-wider text-red-600/80 dark:text-red-300/80">
              {explanationLabel}
            </p>
          )}
          <p className="text-sm text-slate-600 dark:text-slate-300">{explanation}</p>
        </div>
      )}
      <button
        ref={nextRef}
        onClick={onNext}
        className="w-full rounded-xl bg-brand-600 py-3 text-sm font-bold text-white transition-transform hover:bg-brand-700 active:scale-[0.98]"
      >
        {isLast ? "Natijani ko'rish" : "Keyingi savol"}
      </button>
    </div>
  );
}

/** A start screen's "pool not ready" note + primary start button. */
export function GameStartActions({
  loading,
  error,
  resuming,
  onStart,
  label = "Boshlash",
}: {
  loading: boolean;
  error: boolean;
  resuming: boolean;
  onStart: () => void;
  label?: string;
}) {
  return (
    <>
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">
          Savollar hozircha tayyor emas. Sahifani yangilab qayta urinib ko'ring.
        </p>
      )}
      <button
        onClick={onStart}
        disabled={loading || error}
        className="w-full rounded-xl bg-brand-600 py-3 text-sm font-bold text-white shadow-sm transition-transform hover:bg-brand-700 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Tayyorlanmoqda..." : resuming ? "Davom ettirish" : label}
      </button>
    </>
  );
}
