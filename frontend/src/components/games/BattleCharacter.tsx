import { Scale, Shield, Sparkles, Zap, type LucideIcon } from "lucide-react";
import { useId } from "react";

/** Jang maydoni's fighters — one parametric armored-figure drawing, varied
 * per character by palette, build and helmet crest, so a new fighter is just
 * another entry in `FIGHTERS`. Choosing one is purely cosmetic: every fighter
 * deals the same server-defined damage.
 *
 * Poses are CSS animations on the wrapper (idle bob, attack lunge, hit
 * knock-back with a shield flash, victory lift, defeat slump) plus a strike
 * swing on the front arm — no game engine, no image assets. */

export type FighterPose = "idle" | "attack" | "hit" | "victory" | "defeat";

type Crest = "fin" | "plate" | "halo" | "horns" | "antenna";

export interface Fighter {
  id: string;
  name: string;
  trait: string;
  traitIcon: LucideIcon;
  armor: string;
  armorLight: string;
  armorDark: string;
  accent: string;
  /** Shoulder/chest bulk multiplier. */
  bulk: number;
  crest: Crest;
}

export const FIGHTERS: Fighter[] = [
  {
    id: "nova",
    name: "NOVA",
    trait: "Tezlik",
    traitIcon: Zap,
    armor: "#1e293b",
    armorLight: "#475569",
    armorDark: "#0f172a",
    accent: "#22d3ee",
    bulk: 0.9,
    crest: "fin",
  },
  {
    id: "titan",
    name: "TITAN",
    trait: "Kuch",
    traitIcon: Shield,
    armor: "#1e3a8a",
    armorLight: "#3b82f6",
    armorDark: "#172554",
    accent: "#93c5fd",
    bulk: 1.3,
    crest: "plate",
  },
  {
    id: "pulse",
    name: "PULSE",
    trait: "Energiya",
    traitIcon: Sparkles,
    armor: "#2e1065",
    armorLight: "#7c3aed",
    armorDark: "#1e0a45",
    accent: "#c084fc",
    bulk: 1,
    crest: "halo",
  },
  {
    id: "vector",
    name: "VECTOR",
    trait: "Muvozanat",
    traitIcon: Scale,
    armor: "#134e4a",
    armorLight: "#14b8a6",
    armorDark: "#042f2e",
    accent: "#5eead4",
    bulk: 1.1,
    crest: "horns",
  },
];

export const OPPONENT: Fighter = {
  id: "sentinel",
  name: "SENTINEL",
  trait: "AI raqib",
  traitIcon: Shield,
  armor: "#292524",
  armorLight: "#57534e",
  armorDark: "#0c0a09",
  accent: "#f59e0b",
  bulk: 1.2,
  crest: "antenna",
};

export function fighterById(id: string | null | undefined): Fighter {
  return FIGHTERS.find((f) => f.id === id) ?? FIGHTERS[0];
}

const POSE_CLASS: Record<FighterPose, string> = {
  idle: "animate-fighter-idle",
  attack: "animate-fighter-attack",
  hit: "animate-fighter-hit",
  victory: "animate-fighter-victory",
  defeat: "animate-fighter-defeat",
};

export function BattleCharacter({
  fighter,
  pose = "idle",
  poseKey = 0,
  facing = "right",
  className = "",
}: {
  fighter: Fighter;
  pose?: FighterPose;
  /** Bump to replay the same pose (two attacks in a row). */
  poseKey?: number;
  facing?: "left" | "right";
  className?: string;
}) {
  return (
    <div className={`relative ${className}`} style={facing === "left" ? { transform: "scaleX(-1)" } : undefined}>
      <div key={`${pose}-${poseKey}`} className={`h-full w-full motion-reduce:animate-none ${POSE_CLASS[pose]}`}>
        <FighterSvg fighter={fighter} striking={pose === "attack"} glowing={pose === "victory" || pose === "attack"} />
        {pose === "hit" && (
          <span
            className="pointer-events-none absolute inset-[6%_12%_14%_12%] animate-shield-flash rounded-[45%] border-2 motion-reduce:animate-none"
            style={{
              borderColor: fighter.accent,
              boxShadow: `0 0 24px ${fighter.accent}, inset 0 0 24px ${fighter.accent}66`,
            }}
          />
        )}
      </div>
    </div>
  );
}

function FighterSvg({ fighter: f, striking, glowing }: { fighter: Fighter; striking: boolean; glowing: boolean }) {
  const id = useId().replace(/:/g, "");
  const b = f.bulk;
  const robot = f.crest === "antenna";

  return (
    <svg viewBox="0 0 140 200" className="h-full w-full overflow-visible" aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-armor`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor={f.armorLight} />
          <stop offset="55%" stopColor={f.armor} />
          <stop offset="100%" stopColor={f.armorDark} />
        </linearGradient>
        <linearGradient id={`${id}-edge`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="white" stopOpacity="0.35" />
          <stop offset="100%" stopColor="white" stopOpacity="0" />
        </linearGradient>
        <radialGradient id={`${id}-glow`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={f.accent} stopOpacity="0.9" />
          <stop offset="100%" stopColor={f.accent} stopOpacity="0" />
        </radialGradient>
        <filter id={`${id}-bloom`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="1.6" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Ground shadow + aura */}
      <ellipse cx="72" cy="192" rx="40" ry="6" fill="black" opacity="0.5" />
      <ellipse
        cx="72"
        cy="110"
        rx="58"
        ry="80"
        fill={`url(#${id}-glow)`}
        opacity={glowing ? 0.28 : 0.1}
        style={{ transition: "opacity 0.3s" }}
      />

      {/* NOVA's scarf trails behind */}
      {f.crest === "fin" && (
        <path d="M64 58 Q44 62 30 78 Q40 70 52 70 Q38 80 34 92 Q50 76 66 66 Z" fill={f.accent} opacity="0.55" />
      )}

      {/* Back leg + boot */}
      <path d="M55 115 L72 118 L66 154 L63 182 L47 182 L50 152 Z" fill={f.armorDark} />
      <path d="M44 180 L63 180 L63 190 L41 190 Q40 184 44 180 Z" fill={f.armor} />

      {/* Back arm */}
      <g>
        <path d="M52 70 L44 72 L37 100 L41 116 L50 115 L53 99 Z" fill={f.armorDark} />
        <circle cx="44" cy="118" r="5.5" fill={f.armor} />
      </g>

      {/* Front leg + boot */}
      <path d="M70 116 L90 118 L91 152 L95 180 L79 181 L74 154 Z" fill={`url(#${id}-armor)`} />
      <rect x="79" y="146" width="10" height="7" rx="2" fill={f.accent} opacity="0.75" filter={`url(#${id}-bloom)`} />
      <path d="M77 179 L98 179 Q102 186 97 190 L77 190 Z" fill={f.armorLight} />
      <path d="M77 179 L98 179 L98 181 L77 181 Z" fill={f.accent} opacity="0.6" />

      {/* Torso */}
      <g transform={`translate(72 90) scale(${0.92 + b * 0.08} 1) translate(-72 -90)`}>
        <path d="M50 66 Q71 57 93 66 L96 100 Q93 119 72 121 Q52 119 48 100 Z" fill={`url(#${id}-armor)`} />
        <path d="M50 66 Q71 57 93 66 L92 74 Q71 66 52 74 Z" fill={`url(#${id}-edge)`} />
        <path d="M60 78 L72 90 L84 78" stroke={f.armorDark} strokeWidth="2" fill="none" opacity="0.8" />
        <path d="M58 104 L72 110 L86 104" stroke={f.armorLight} strokeWidth="1.5" fill="none" opacity="0.5" />
        {/* Energy core */}
        <circle cx="72" cy="92" r="11" fill={`url(#${id}-glow)`} opacity={glowing ? 1 : 0.7} />
        {robot ? (
          <rect x="66" y="86" width="12" height="12" rx="2" fill={f.accent} filter={`url(#${id}-bloom)`} />
        ) : (
          <circle cx="72" cy="92" r="5.5" fill={f.accent} filter={`url(#${id}-bloom)`} />
        )}
        {/* Belt */}
        <rect x="51" y="112" width="42" height="7" rx="2" fill={f.armorLight} />
        <rect x="68" y="112" width="8" height="7" rx="1.5" fill={f.accent} opacity="0.85" />
      </g>

      {/* Back pauldron */}
      <ellipse cx="51" cy="69" rx={10 * b} ry={8 * b} fill={f.armorDark} />

      {/* Neck + head */}
      <rect x="66" y="50" width="12" height="11" rx="2" fill={f.armorDark} />
      {robot ? (
        <g>
          <path d="M58 22 H90 L94 50 H56 Z" fill={`url(#${id}-armor)`} />
          <path d="M58 22 H90 L91 28 H57 Z" fill={`url(#${id}-edge)`} />
          <rect x="64" y="32" width="30" height="7" rx="3.5" fill={f.accent} filter={`url(#${id}-bloom)`} />
          <rect x="72" y="8" width="3" height="15" fill={f.armorLight} />
          <circle
            cx="73.5"
            cy="7"
            r="3.2"
            fill={f.accent}
            filter={`url(#${id}-bloom)`}
            className="animate-pulse motion-reduce:animate-none"
          />
        </g>
      ) : (
        <g>
          <path d="M59 40 Q59 18 76 16 Q94 18 93 38 L91 50 Q76 57 61 51 Z" fill={`url(#${id}-armor)`} />
          <path d="M62 30 Q64 20 76 18 Q88 19 91 28 Q76 24 62 30 Z" fill={`url(#${id}-edge)`} />
          {/* Visor */}
          <path d="M70 32 Q84 28 93 33 L92 42 Q82 39 70 42 Z" fill={f.accent} filter={`url(#${id}-bloom)`} />
          <path d="M72 34 Q82 31 90 34" stroke="white" strokeOpacity="0.7" strokeWidth="1" fill="none" />
          {f.crest === "fin" && <path d="M66 20 L50 6 L60 8 L74 17 Z" fill={f.armorLight} />}
          {f.crest === "plate" && <path d="M58 24 H92 L93 29 H57 Z" fill={f.armorLight} />}
          {f.crest === "halo" && (
            <ellipse
              cx="76"
              cy="9"
              rx="17"
              ry="4.5"
              fill="none"
              stroke={f.accent}
              strokeWidth="2"
              filter={`url(#${id}-bloom)`}
            />
          )}
          {f.crest === "horns" && (
            <g fill={f.accent} filter={`url(#${id}-bloom)`}>
              <path d="M64 24 L56 9 L68 21 Z" />
              <path d="M86 21 L95 7 L90 24 Z" />
            </g>
          )}
        </g>
      )}

      {/* Front arm — swings forward on a strike */}
      <g
        className={striking ? "animate-arm-strike motion-reduce:animate-none" : undefined}
        style={{ transformBox: "view-box", transformOrigin: "92px 70px" }}
      >
        <path d="M86 68 L99 70 L103 94 L92 97 Z" fill={`url(#${id}-armor)`} />
        <path d="M92 92 L105 91 L120 103 L113 112 L96 105 Z" fill={f.armor} />
        <circle cx="119" cy="108" r="13" fill={`url(#${id}-glow)`} opacity={striking ? 1 : 0.55} />
        <circle cx="119" cy="108" r="7" fill={f.armorLight} />
        <circle cx="119" cy="108" r="3.5" fill={f.accent} filter={`url(#${id}-bloom)`} />
      </g>

      {/* Front pauldron (drawn last, on top of the arm) */}
      <path
        d={`M${92 - 12 * b} 70 Q92 ${58 - 4 * b} ${92 + 12 * b} 70 L${92 + 9 * b} 78 Q92 ${72} ${92 - 9 * b} 78 Z`}
        fill={`url(#${id}-armor)`}
      />
      <path
        d={`M${92 - 10 * b} 69 Q92 ${60 - 4 * b} ${92 + 10 * b} 69`}
        stroke={f.accent}
        strokeOpacity="0.7"
        strokeWidth="1.5"
        fill="none"
      />

      {f.crest === "halo" && (
        <circle
          cx="30"
          cy="96"
          r="5"
          fill={f.accent}
          opacity="0.8"
          filter={`url(#${id}-bloom)`}
          className="animate-pulse motion-reduce:animate-none"
        />
      )}
    </svg>
  );
}
