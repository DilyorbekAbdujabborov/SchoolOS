import { useId } from "react";

/** Minora qurish's center stage: a glass-and-steel high-rise drawn in SVG, one
 * floor per correct answer. Unbuilt floors stay visible as a faint dashed
 * scaffold so the student always sees how tall the tower *could* get; the
 * newest floor drops into place with a short flash, and a finished game
 * crowns the tower with a roof and a beacon. */

const VIEW_W = 200;
const VIEW_H = 300;
const GROUND_Y = 286;
const LOBBY_H = 18;
const FLOOR_H = 22;
const FLOOR_X = 54;
const FLOOR_W = 92;
const WINDOWS_PER_FLOOR = 4;

function floorTop(index: number): number {
  return GROUND_Y - LOBBY_H - (index + 1) * FLOOR_H;
}

// Deterministic "lights on" pattern — stable across re-renders, varied enough
// not to look like a grid of identical boxes.
function isLit(floor: number, window: number): boolean {
  return (floor * 7 + window * 3) % 5 < 2;
}

// Background skyline blocks: [x, width, height].
const SKYLINE: [number, number, number][] = [
  [0, 18, 70],
  [16, 22, 110],
  [36, 14, 54],
  [150, 16, 90],
  [164, 22, 128],
  [184, 16, 64],
];

export function TowerScene({
  floors,
  maxFloors,
  newFloorKey,
  complete = false,
  compact = false,
}: {
  floors: number;
  maxFloors: number;
  /** Changes each time a floor is added, so only that floor animates in. */
  newFloorKey?: number;
  complete?: boolean;
  compact?: boolean;
}) {
  const id = useId().replace(/:/g, "");
  const built = Math.max(0, Math.min(floors, maxFloors));
  const crownY = floorTop(built - 1);

  return (
    <svg
      viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
      className={`mx-auto block h-full w-auto max-w-full ${compact ? "max-h-56" : ""}`}
      role="img"
      aria-label={`Minora: ${built} qavat`}
    >
      <defs>
        <linearGradient id={`${id}-facade`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#2563eb" />
          <stop offset="45%" stopColor="#1e40af" />
          <stop offset="100%" stopColor="#172554" />
        </linearGradient>
        <linearGradient id={`${id}-ledge`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#bfdbfe" />
          <stop offset="100%" stopColor="#60a5fa" />
        </linearGradient>
        <linearGradient id={`${id}-glass`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#93c5fd" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#1e3a8a" stopOpacity="0.9" />
        </linearGradient>
        <linearGradient id={`${id}-lit`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#fef3c7" />
          <stop offset="100%" stopColor="#f59e0b" />
        </linearGradient>
        <linearGradient id={`${id}-lobby`} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#334155" />
          <stop offset="100%" stopColor="#0f172a" />
        </linearGradient>
        <radialGradient id={`${id}-halo`} cx="50%" cy="85%" r="60%">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Atmosphere + distant skyline */}
      <rect x="0" y="0" width={VIEW_W} height={VIEW_H} fill={`url(#${id}-halo)`} />
      {SKYLINE.map(([x, w, h]) => (
        <rect key={x} x={x} y={GROUND_Y - h} width={w} height={h} fill="#1e293b" opacity="0.55" />
      ))}

      {/* Scaffold for floors not built yet */}
      {Array.from({ length: maxFloors - built }, (_, k) => {
        const index = built + k;
        return (
          <rect
            key={`ghost-${index}`}
            x={FLOOR_X + 0.5}
            y={floorTop(index) + 0.5}
            width={FLOOR_W - 1}
            height={FLOOR_H - 1}
            fill="none"
            stroke="#64748b"
            strokeOpacity="0.35"
            strokeDasharray="3 3"
          />
        );
      })}

      <g className={complete ? "animate-tower-glow" : undefined}>
        {/* Ground */}
        <rect x="0" y={GROUND_Y} width={VIEW_W} height={VIEW_H - GROUND_Y} fill="#020617" />
        <rect x="0" y={GROUND_Y} width={VIEW_W} height="1" fill="#334155" />
        <ellipse cx={VIEW_W / 2} cy={GROUND_Y + 2} rx="66" ry="3" fill="black" opacity="0.45" />

        {/* Lobby */}
        <rect x="44" y={GROUND_Y - LOBBY_H} width="112" height={LOBBY_H} fill={`url(#${id}-lobby)`} />
        <rect x="41" y={GROUND_Y - LOBBY_H - 2} width="118" height="3" rx="1" fill={`url(#${id}-ledge)`} />
        <rect x="90" y={GROUND_Y - 12} width="20" height="12" fill={`url(#${id}-lit)`} opacity="0.9" />
        <rect x="99.5" y={GROUND_Y - 12} width="1" height="12" fill="#78350f" opacity="0.5" />
        <rect x="86" y={GROUND_Y - 14} width="28" height="2" fill="#94a3b8" />
        {[52, 68, 120, 136].map((x) => (
          <rect key={x} x={x} y={GROUND_Y - 12} width="12" height="8" fill={`url(#${id}-glass)`} />
        ))}

        {Array.from({ length: built }, (_, index) => (
          <Floor
            key={index === built - 1 && newFloorKey !== undefined ? `floor-${index}-${newFloorKey}` : `floor-${index}`}
            index={index}
            id={id}
            animate={index === built - 1 && newFloorKey !== undefined && newFloorKey > 0}
          />
        ))}

        {complete && built > 0 && (
          <g className="animate-floor-drop" style={{ transformBox: "fill-box", transformOrigin: "center bottom" }}>
            <path
              d={`M${FLOOR_X - 2} ${crownY} L${FLOOR_X + 12} ${crownY - 9} L${FLOOR_X + FLOOR_W - 12} ${crownY - 9} L${FLOOR_X + FLOOR_W + 2} ${crownY} Z`}
              fill="#1e3a8a"
            />
            <rect x={FLOOR_X + 12} y={crownY - 10} width={FLOOR_W - 24} height="2" fill={`url(#${id}-ledge)`} />
            <rect x="98.5" y={crownY - 34} width="3" height="24" fill="#94a3b8" />
            <circle cx="100" cy={crownY - 36} r="3" fill="#f59e0b" className="animate-pulse" />
          </g>
        )}
      </g>
    </svg>
  );
}

function Floor({ index, id, animate }: { index: number; id: string; animate: boolean }) {
  const y = floorTop(index);
  return (
    <g
      className={animate ? "animate-floor-drop" : undefined}
      style={{ transformBox: "fill-box", transformOrigin: "center bottom" }}
    >
      <rect x={FLOOR_X} y={y} width={FLOOR_W} height={FLOOR_H} fill={`url(#${id}-facade)`} />
      {/* Pilasters between window bays */}
      {[78, 98, 118].map((x) => (
        <rect key={x} x={x} y={y + 3} width="1.5" height={FLOOR_H - 3} fill="white" opacity="0.07" />
      ))}
      {Array.from({ length: WINDOWS_PER_FLOOR }, (_, j) => {
        const x = FLOOR_X + 7 + j * 20;
        const lit = isLit(index, j);
        return (
          <g key={j}>
            <rect x={x} y={y + 7} width="15" height="11" rx="0.8" fill={`url(#${id}-${lit ? "lit" : "glass"})`} />
            <rect x={x + 7} y={y + 7} width="0.8" height="11" fill="#0f172a" opacity="0.35" />
            <rect x={x} y={y + 7} width="15" height="1.2" fill="white" opacity="0.18" />
          </g>
        );
      })}
      {/* Shaded east face + slab shadow */}
      <rect x={FLOOR_X + FLOOR_W - 8} y={y} width="8" height={FLOOR_H} fill="black" opacity="0.22" />
      <rect x={FLOOR_X} y={y + FLOOR_H - 2} width={FLOOR_W} height="2" fill="black" opacity="0.25" />
      {/* Floor slab / ledge */}
      <rect x={FLOOR_X - 3} y={y} width={FLOOR_W + 6} height="3" rx="1" fill={`url(#${id}-ledge)`} />
      {animate && (
        <rect
          x={FLOOR_X - 3}
          y={y}
          width={FLOOR_W + 6}
          height={FLOOR_H}
          fill="#bfdbfe"
          className="animate-floor-flash"
        />
      )}
    </g>
  );
}
