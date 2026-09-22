type Variant = "player" | "ai";

const GRADIENT: Record<Variant, { from: string; to: string }> = {
  player: { from: "#a78bfa", to: "#6f57cf" },
  ai: { from: "#fbbf24", to: "#d97706" },
};

/** An abstract, Olympic-pictogram-style figure in a pulling lunge — no faces, no
 * clipart. The whole silhouette rotates around its feet to sell "leaning into
 * the pull" as the rope shifts, mirrored so each figure's arm always reaches
 * toward the rope at center. */
function Figure({ variant, lean }: { variant: Variant; lean: number }) {
  const gradientId = `rope-fig-${variant}`;
  const mirror = variant === "ai";
  const g = GRADIENT[variant];

  return (
    <svg
      viewBox="0 0 64 96"
      className="h-16 w-11 shrink-0 sm:h-24 sm:w-16"
      style={{
        transformOrigin: "50% 94%",
        transform: `rotate(${lean}deg) ${mirror ? "scaleX(-1)" : ""}`,
        transition: "transform 0.5s cubic-bezier(0.34,1.56,0.64,1)",
      }}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={g.from} />
          <stop offset="100%" stopColor={g.to} />
        </linearGradient>
      </defs>
      <ellipse cx="32" cy="93" rx="18" ry="3" fill="black" opacity="0.18" />
      <path d="M32 58 L18 90 L27 92 L37 60 Z" fill={`url(#${gradientId})`} opacity="0.88" />
      <path d="M32 58 L45 88 L54 85 L39 57 Z" fill={`url(#${gradientId})`} />
      <path d="M21 28 Q32 21 43 28 L41 62 L23 62 Z" fill={`url(#${gradientId})`} />
      <path d="M40 34 L59 43 L56 50 L38 43 Z" fill={`url(#${gradientId})`} />
      <circle cx="32" cy="15" r="11" fill={`url(#${gradientId})`} />
    </svg>
  );
}

function clamp(value: number): number {
  return Math.min(100, Math.max(0, value));
}

/** 0 = fully pulled to the player's side, 100 = fully pulled to the AI's side. */
export function RopeArena({ position, active }: { position: number; active: boolean }) {
  const clamped = clamp(position);
  const tilt = (50 - clamped) / 50; // 1 = player winning, -1 = AI winning

  return (
    <div className="rounded-2xl bg-gradient-to-b from-slate-900 to-slate-950 p-4 sm:p-6">
      <div className="flex items-end justify-between gap-2 sm:gap-6">
        <Figure variant="player" lean={-tilt * 16} />
        <div className="mb-8 flex-1">
          <div className="relative h-4 w-full rounded-full bg-slate-800 shadow-[inset_0_1px_3px_rgba(0,0,0,0.5)]">
            <div className="absolute inset-y-0 left-0 w-[10%] rounded-l-full bg-brand-500/25" />
            <div className="absolute inset-y-0 right-0 w-[10%] rounded-r-full bg-amber-500/25" />
            <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-slate-600/70" />
            <div
              className="absolute top-1/2 h-6 w-6 -translate-y-1/2 -translate-x-1/2 rounded-full border-[3px] border-slate-950 bg-gradient-to-br from-white to-slate-300 shadow-lg transition-[left] duration-700 ease-out"
              style={{ left: `${clamped}%` }}
            >
              {active && <span className="absolute inset-0 animate-ping rounded-full bg-white/60" />}
            </div>
          </div>
        </div>
        <Figure variant="ai" lean={-tilt * 16} />
      </div>
    </div>
  );
}
