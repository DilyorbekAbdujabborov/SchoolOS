import { Lock, LockOpen, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";

/** Kodni buzish's center stage — a "security terminal" guarding a secret
 * code, one segment per question. Locked segments sit dark behind a padlock;
 * a segment unlocked by a correct answer decrypts in (a quick character
 * scramble, a flip, a blue glow). The security-level meter fills with each
 * correct answer and marks the unlock threshold, so the student always sees
 * how close they are.
 *
 * The component only ever receives segments the server already revealed —
 * `null` means "still locked" and there's no secret to leak client-side. */

export type TerminalState = "active" | "unlocked" | "locked";

// Pure visual noise for the decrypt effect — unrelated to the real code.
const NOISE = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ#$%&@";

function ScrambleChar({ value, delayMs = 0 }: { value: string; delayMs?: number }) {
  const [shown, setShown] = useState(() => NOISE[Math.floor(Math.random() * NOISE.length)]);

  useEffect(() => {
    let ticks = 0;
    let interval: ReturnType<typeof setInterval> | undefined;
    const start = setTimeout(() => {
      interval = setInterval(() => {
        ticks += 1;
        if (ticks >= 9) {
          setShown(value);
          clearInterval(interval);
        } else {
          setShown(NOISE[Math.floor(Math.random() * NOISE.length)]);
        }
      }, 45);
    }, delayMs);
    return () => {
      clearTimeout(start);
      clearInterval(interval);
    };
  }, [value, delayMs]);

  return <>{shown}</>;
}

function CodeCell({
  value,
  index,
  isNew,
  finale,
  state,
}: {
  value: string | null;
  index: number;
  isNew: boolean;
  finale: boolean;
  state: TerminalState;
}) {
  if (value === null) {
    return (
      <div
        className={`flex aspect-[4/5] items-center justify-center rounded-xl border bg-slate-900/80 shadow-[inset_0_2px_6px_rgba(0,0,0,0.6)] ${
          state === "locked" ? "border-red-500/25" : "border-slate-700/80"
        }`}
        aria-label={`${index + 1}-segment: yopiq`}
      >
        <Lock size={14} className={state === "locked" ? "text-red-400/60" : "text-slate-500"} />
      </div>
    );
  }

  const animate = isNew || finale;
  const delay = finale ? index * 70 : 0;
  const tone =
    state === "unlocked"
      ? "border-emerald-400/70 bg-emerald-500/15 text-emerald-100 shadow-[0_0_14px_rgba(16,185,129,0.35)]"
      : "border-brand-400/70 bg-brand-500/15 text-sky-100 shadow-[0_0_14px_rgba(59,130,246,0.3)]";

  return (
    <div
      className={`relative flex aspect-[4/5] items-center justify-center rounded-xl border font-mono text-xl font-bold sm:text-2xl ${tone} ${
        animate ? "animate-code-reveal" : ""
      }`}
      style={animate ? { animationDelay: `${delay}ms` } : undefined}
      aria-label={`${index + 1}-segment: ${value}`}
    >
      {isNew && <span className="absolute inset-0 animate-segment-glow rounded-xl" />}
      <span className="relative">{animate ? <ScrambleChar value={value} delayMs={delay} /> : value}</span>
      <span className="absolute inset-x-2 top-1 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />
    </div>
  );
}

export function SecurityTerminal({
  code,
  correctCount,
  answeredCount,
  total,
  unlockPercent,
  state = "active",
  newSegmentIndex,
  alertKey = 0,
}: {
  code: (string | null)[];
  correctCount: number;
  answeredCount: number;
  total: number;
  unlockPercent: number;
  state?: TerminalState;
  /** The segment the latest correct answer unlocked — only it animates in. */
  newSegmentIndex?: number | null;
  /** Bumped on every wrong answer to replay the red alert flash. */
  alertKey?: number;
}) {
  const needed = Math.ceil((total * unlockPercent) / 100);
  const stillNeeded = Math.max(0, needed - correctCount);
  const remaining = total - answeredCount;
  const finale = state === "unlocked";

  const status =
    state === "unlocked"
      ? { text: "ACCESS GRANTED", dot: "bg-emerald-400", color: "text-emerald-300" }
      : state === "locked"
        ? { text: "ACCESS DENIED", dot: "bg-red-400", color: "text-red-300" }
        : { text: "DECRYPTING", dot: "bg-brand-400 animate-pulse", color: "text-sky-300" };

  const hint =
    state === "unlocked"
      ? "Barcha segmentlar ochildi — kod buzildi."
      : state === "locked"
        ? `Kodni ochish uchun ${needed} ta to'g'ri javob kerak edi.`
        : stillNeeded === 0
          ? "Ochish chegarasidan o'tdingiz — kod albatta ochiladi!"
          : stillNeeded > remaining
            ? `${unlockPercent}% ga endi yetib bo'lmaydi, lekin har bir segment hisobga olinadi.`
            : `Kodni ochish uchun yana ${stillNeeded} ta to'g'ri javob kerak · ${remaining} ta savol qoldi`;

  return (
    <div
      key={alertKey}
      className={`relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900 to-slate-950 p-4 sm:p-6 ${
        alertKey > 0 && state === "active" ? "animate-alert-flash" : ""
      }`}
      style={{
        backgroundImage:
          "linear-gradient(rgba(59,130,246,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(59,130,246,0.05) 1px, transparent 1px)",
        backgroundSize: "22px 22px",
      }}
    >
      {state === "active" && (
        <div className="pointer-events-none absolute inset-x-0 top-0 h-1/5 animate-scan bg-gradient-to-b from-transparent via-brand-400/[0.07] to-transparent" />
      )}

      {/* Header */}
      <div className="relative flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.3em] text-slate-500">
            Security terminal
          </p>
          <p className={`mt-1 flex items-center gap-2 font-mono text-xs font-bold tracking-widest ${status.color}`}>
            <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${status.dot}`} />
            {status.text}
          </p>
        </div>
        <LockBadge state={state} />
      </div>

      {/* Security level */}
      <div className="relative mt-5">
        <div className="flex items-baseline justify-between font-mono text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-500">
          <span>Security level</span>
          <span className="text-slate-300">
            {correctCount}/{total}
          </span>
        </div>
        <div className="relative mt-2 flex gap-1">
          {Array.from({ length: total }, (_, i) => (
            <div
              key={i}
              className={`h-2 flex-1 rounded-sm transition-colors duration-500 ${
                i < correctCount
                  ? state === "unlocked"
                    ? "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.6)]"
                    : "bg-brand-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]"
                  : "bg-slate-800"
              }`}
            />
          ))}
        </div>
        <div className="relative mt-1 h-4">
          <span
            className="absolute -translate-x-1/2 font-mono text-[10px] font-bold text-amber-400/90"
            style={{ left: `${(needed / total) * 100}%` }}
          >
            ▲ {unlockPercent}%
          </span>
        </div>
      </div>

      {/* Secret code */}
      <div className="relative mt-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.25em] text-slate-500">Secret code</p>
        <div className="mt-2 grid grid-cols-5 gap-2 [perspective:600px] sm:grid-cols-10 sm:gap-1.5 md:gap-2">
          {code.map((value, i) => (
            <CodeCell
              key={`${i}-${value ?? "locked"}`}
              value={value}
              index={i}
              isNew={i === newSegmentIndex}
              finale={finale}
              state={state}
            />
          ))}
        </div>
      </div>

      <p className="relative mt-4 text-center text-xs text-slate-400">{hint}</p>
    </div>
  );
}

function LockBadge({ state }: { state: TerminalState }) {
  if (state === "unlocked") {
    return (
      <span className="flex h-12 w-12 shrink-0 animate-pop-in items-center justify-center rounded-2xl border border-emerald-400/50 bg-emerald-500/15 text-emerald-300 shadow-[0_0_24px_rgba(16,185,129,0.45)]">
        <LockOpen size={22} />
      </span>
    );
  }
  if (state === "locked") {
    return (
      <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-red-400/40 bg-red-500/10 text-red-300">
        <ShieldAlert size={22} />
      </span>
    );
  }
  return (
    <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-brand-400/40 bg-brand-500/10 text-sky-300 shadow-[0_0_20px_rgba(59,130,246,0.3)]">
      <Lock size={22} />
    </span>
  );
}
