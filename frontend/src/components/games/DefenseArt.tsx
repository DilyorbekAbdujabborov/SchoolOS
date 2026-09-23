import { useId } from "react";

import type { DefenseBoost, DefenseEnemyType } from "../../types";

/** Tower Defense's artwork — the player's defense tower and the four enemy
 * drones, as lightweight inline SVG. Stylized machines, nothing scary: the
 * enemies are geometric drones with a glowing core, drawn facing the base. */

const TOWER_PALETTE: Record<"normal" | "POWER_BOOST" | "OVERCHARGE", { core: string; glow: string; ring: string }> = {
  normal: { core: "#22d3ee", glow: "#38bdf8", ring: "#7dd3fc" },
  POWER_BOOST: { core: "#fbbf24", glow: "#f59e0b", ring: "#fde68a" },
  OVERCHARGE: { core: "#e9d5ff", glow: "#a855f7", ring: "#f0abfc" },
};

export function DefenseTower({
  boost,
  charging = false,
  className = "",
}: {
  boost: DefenseBoost;
  /** The moment of a shot — the crystal flares. */
  charging?: boolean;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  const palette = TOWER_PALETTE[boost ?? "normal"];
  const rings = boost === "OVERCHARGE" ? 3 : boost === "POWER_BOOST" ? 2 : 1;

  return (
    <svg viewBox="0 0 120 220" className={`overflow-visible ${className}`} aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-steel`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#475569" />
          <stop offset="45%" stopColor="#1e293b" />
          <stop offset="100%" stopColor="#0b1220" />
        </linearGradient>
        <radialGradient id={`${id}-glow`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={palette.glow} stopOpacity="0.9" />
          <stop offset="100%" stopColor={palette.glow} stopOpacity="0" />
        </radialGradient>
        <linearGradient id={`${id}-crystal`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="white" />
          <stop offset="55%" stopColor={palette.core} />
          <stop offset="100%" stopColor={palette.glow} />
        </linearGradient>
        <filter id={`${id}-bloom`} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="2" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Ground glow + plinth */}
      <ellipse cx="60" cy="208" rx="54" ry="9" fill={palette.glow} opacity="0.25" />
      <path d="M14 206 L24 188 H96 L106 206 Z" fill={`url(#${id}-steel)`} />
      <path d="M24 188 H96 L92 182 H28 Z" fill="#64748b" />
      <rect x="14" y="204" width="92" height="3" fill={palette.core} opacity="0.7" filter={`url(#${id}-bloom)`} />

      {/* Pylon */}
      <path d="M36 182 L44 84 H76 L84 182 Z" fill={`url(#${id}-steel)`} />
      <path d="M44 84 H76 L74 92 H46 Z" fill="#64748b" />
      {[110, 136, 162].map((y) => (
        <rect key={y} x="42" y={y} width="36" height="2" fill="#0f172a" opacity="0.6" />
      ))}
      {/* Energy conduit */}
      <rect
        x="58"
        y="92"
        width="4"
        height="90"
        rx="2"
        fill={palette.core}
        opacity="0.85"
        filter={`url(#${id}-bloom)`}
      />
      {/* Side fins */}
      <path d="M36 150 L22 176 L38 176 Z" fill="#334155" />
      <path d="M84 150 L98 176 L82 176 Z" fill="#1e293b" />

      {/* Emitter cradle */}
      <path d="M40 84 L30 66 H44 L52 80 Z" fill="#334155" />
      <path d="M80 84 L90 66 H76 L68 80 Z" fill="#1e293b" />

      {/* Crystal + rings */}
      <circle
        cx="60"
        cy="46"
        r={charging ? 42 : boost ? 34 : 28}
        fill={`url(#${id}-glow)`}
        opacity={charging ? 1 : 0.75}
        style={{ transition: "r 0.3s ease, opacity 0.3s ease" }}
      />
      <g
        className="animate-[spin_9s_linear_infinite] motion-reduce:animate-none"
        style={{ transformBox: "view-box", transformOrigin: "60px 46px" }}
      >
        {Array.from({ length: rings }, (_, i) => (
          <ellipse
            key={i}
            cx="60"
            cy="46"
            rx={26 + i * 7}
            ry={8 + i * 2}
            fill="none"
            stroke={palette.ring}
            strokeOpacity={0.7 - i * 0.15}
            strokeWidth="1.5"
            strokeDasharray="10 6"
            transform={`rotate(${i * 25} 60 46)`}
          />
        ))}
      </g>
      <path
        d="M60 18 L74 46 L60 76 L46 46 Z"
        fill={`url(#${id}-crystal)`}
        filter={`url(#${id}-bloom)`}
        className={charging ? "animate-pulse" : undefined}
      />
      <path d="M60 18 L74 46 L60 46 Z" fill="white" opacity="0.35" />
    </svg>
  );
}

/** One enemy drone. `shielded` shows the energy bubble while its shield holds. */
export function DefenseEnemyArt({
  type,
  shielded = false,
  className = "",
}: {
  type: DefenseEnemyType;
  shielded?: boolean;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 100 100" className={`overflow-visible ${className}`} aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-hull`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#475569" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
        <radialGradient id={`${id}-core`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="white" />
          <stop offset="40%" stopColor={type === "tank" ? "#f59e0b" : "#e879f9"} />
          <stop offset="100%" stopColor={type === "tank" ? "#f59e0b" : "#a855f7"} stopOpacity="0" />
        </radialGradient>
        <filter id={`${id}-bloom`} x="-60%" y="-60%" width="220%" height="220%">
          <feGaussianBlur stdDeviation="1.8" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <ellipse cx="50" cy="94" rx="26" ry="4" fill="black" opacity="0.45" />
      {type === "scout" && <Scout id={id} />}
      {type === "shield" && <ShieldDrone id={id} />}
      {type === "tank" && <Tank id={id} />}
      {type === "boss" && <Boss id={id} />}
      {shielded && (
        <circle
          cx="50"
          cy="50"
          r="44"
          fill="#c084fc"
          fillOpacity="0.12"
          stroke="#e9d5ff"
          strokeOpacity="0.7"
          strokeWidth="1.5"
          strokeDasharray="4 3"
          filter={`url(#${id}-bloom)`}
        />
      )}
    </svg>
  );
}

// Enemies face left — toward the base.
function Scout({ id }: { id: string }) {
  return (
    <g>
      {/* thruster trail */}
      <path d="M70 50 L96 44 L96 56 Z" fill="#e879f9" opacity="0.35" filter={`url(#${id}-bloom)`} />
      <path d="M58 32 L78 22 L70 44 Z" fill="#334155" />
      <path d="M58 68 L78 78 L70 56 Z" fill="#1e293b" />
      <path d="M16 50 L62 34 L74 50 L62 66 Z" fill={`url(#${id}-hull)`} />
      <path d="M16 50 L62 34 L60 44 Z" fill="white" opacity="0.12" />
      <circle cx="44" cy="50" r="12" fill={`url(#${id}-core)`} />
      <circle cx="44" cy="50" r="4" fill="white" filter={`url(#${id}-bloom)`} />
    </g>
  );
}

function ShieldDrone({ id }: { id: string }) {
  return (
    <g>
      <path
        d="M50 18 L78 34 L78 66 L50 82 L22 66 L22 34 Z"
        fill={`url(#${id}-hull)`}
        stroke="#64748b"
        strokeWidth="1.5"
      />
      <path d="M50 18 L78 34 L50 40 L22 34 Z" fill="white" opacity="0.1" />
      <path d="M22 44 L10 50 L22 56 Z" fill="#e879f9" opacity="0.8" />
      <circle cx="50" cy="52" r="14" fill={`url(#${id}-core)`} />
      <path d="M44 52 L50 44 L56 52 L50 60 Z" fill="white" filter={`url(#${id}-bloom)`} />
    </g>
  );
}

function Tank({ id }: { id: string }) {
  return (
    <g>
      {/* treads */}
      <rect x="10" y="64" width="80" height="20" rx="10" fill="#1e293b" stroke="#475569" strokeWidth="1.5" />
      {[22, 38, 54, 70].map((x) => (
        <circle key={x} cx={x + 4} cy="74" r="5" fill="#334155" />
      ))}
      {/* chassis */}
      <path d="M16 64 L24 44 H78 L86 64 Z" fill={`url(#${id}-hull)`} />
      <path d="M24 44 H78 L76 50 H26 Z" fill="white" opacity="0.1" />
      {/* dome + emitter facing the base */}
      <path d="M36 44 Q50 22 66 44 Z" fill="#334155" />
      <rect x="8" y="38" width="30" height="6" rx="3" fill="#475569" />
      <circle cx="51" cy="40" r="9" fill={`url(#${id}-core)`} />
      <circle cx="10" cy="41" r="3" fill="#f59e0b" filter={`url(#${id}-bloom)`} />
    </g>
  );
}

function Boss({ id }: { id: string }) {
  return (
    <g>
      <circle cx="50" cy="50" r="46" fill="#a855f7" opacity="0.12" filter={`url(#${id}-bloom)`} />
      {/* rotating outer ring */}
      <g
        className="animate-[spin_12s_linear_infinite] motion-reduce:animate-none"
        style={{ transformBox: "view-box", transformOrigin: "50px 50px" }}
      >
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="#c084fc"
          strokeOpacity="0.6"
          strokeWidth="2"
          strokeDasharray="14 8"
        />
        {[0, 90, 180, 270].map((angle) => (
          <path key={angle} d="M50 6 L55 14 L45 14 Z" fill="#e879f9" transform={`rotate(${angle} 50 50)`} />
        ))}
      </g>
      {/* armored octagon */}
      <path
        d="M36 18 H64 L82 36 V64 L64 82 H36 L18 64 V36 Z"
        fill={`url(#${id}-hull)`}
        stroke="#7c3aed"
        strokeWidth="2"
      />
      <path d="M36 18 H64 L82 36 H18 Z" fill="white" opacity="0.08" />
      {[
        [30, 30],
        [70, 30],
        [30, 70],
        [70, 70],
      ].map(([x, y]) => (
        <circle key={`${x}-${y}`} cx={x} cy={y} r="3" fill="#e879f9" filter={`url(#${id}-bloom)`} />
      ))}
      <circle cx="50" cy="50" r="18" fill={`url(#${id}-core)`} className="animate-pulse motion-reduce:animate-none" />
      <circle cx="50" cy="50" r="7" fill="white" filter={`url(#${id}-bloom)`} />
    </g>
  );
}
