import { useId } from "react";

/** Neon Racing's artwork: rear-view hover-racers and the track themes. One
 * parametric car drawing (palette + wing/canopy style), so a new car or AI
 * rival is just another entry; a track is a palette plus one signature scenery
 * feature, so new tracks slot in the same way. Pure inline SVG/CSS — no assets. */

export interface CarDesign {
  id: string;
  name: string;
  tagline: string;
  body: string;
  bodyDark: string;
  accent: string;
  lights: string;
  wing: "high" | "split" | "none";
}

export const PLAYER_CARS: CarDesign[] = [
  {
    id: "nova",
    name: "NOVA GT",
    tagline: "Muvozanatli",
    body: "#1e3a8a",
    bodyDark: "#0b1530",
    accent: "#22d3ee",
    lights: "#67e8f9",
    wing: "high",
  },
  {
    id: "pulse",
    name: "PULSE R",
    tagline: "Tez start",
    body: "#4c1d95",
    bodyDark: "#1e0a45",
    accent: "#c084fc",
    lights: "#f0abfc",
    wing: "split",
  },
  {
    id: "vector",
    name: "VECTOR X",
    tagline: "Aerodinamik",
    body: "#134e4a",
    bodyDark: "#042f2e",
    accent: "#2dd4bf",
    lights: "#5eead4",
    wing: "none",
  },
  {
    id: "titan",
    name: "TITAN S",
    tagline: "Barqaror",
    body: "#1e293b",
    bodyDark: "#020617",
    accent: "#60a5fa",
    lights: "#bfdbfe",
    wing: "high",
  },
];

/** AI rivals, keyed by the server's racer id (apps.games.racing.AI_RACERS). */
export const RIVAL_CARS: Record<string, CarDesign> = {
  volt: {
    id: "volt",
    name: "VOLT",
    tagline: "Balanced",
    body: "#422006",
    bodyDark: "#1c0a02",
    accent: "#fbbf24",
    lights: "#fde68a",
    wing: "high",
  },
  blaze: {
    id: "blaze",
    name: "BLAZE",
    tagline: "High acceleration",
    body: "#7c2d12",
    bodyDark: "#2a0f06",
    accent: "#fb923c",
    lights: "#fdba74",
    wing: "split",
  },
  apex: {
    id: "apex",
    name: "APEX",
    tagline: "High top speed",
    body: "#14532d",
    bodyDark: "#052e16",
    accent: "#4ade80",
    lights: "#bbf7d0",
    wing: "none",
  },
  rogue: {
    id: "rogue",
    name: "ROGUE",
    tagline: "Aggressive rival",
    body: "#701a75",
    bodyDark: "#2e0530",
    accent: "#f472b6",
    lights: "#fbcfe8",
    wing: "split",
  },
};

export function carById(id: string | null | undefined): CarDesign {
  return PLAYER_CARS.find((car) => car.id === id) ?? PLAYER_CARS[0];
}

export function RaceCar({ car, boost = 0, className = "" }: { car: CarDesign; boost?: 0 | 1 | 2; className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 200 120" className={`overflow-visible ${className}`} aria-hidden="true">
      <defs>
        <linearGradient id={`${id}-body`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={car.body} />
          <stop offset="100%" stopColor={car.bodyDark} />
        </linearGradient>
        <linearGradient id={`${id}-glass`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={car.lights} stopOpacity="0.55" />
          <stop offset="100%" stopColor="#020617" stopOpacity="0.9" />
        </linearGradient>
        <radialGradient id={`${id}-glow`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor={car.accent} stopOpacity="0.9" />
          <stop offset="100%" stopColor={car.accent} stopOpacity="0" />
        </radialGradient>
        <filter id={`${id}-bloom`} x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="2" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* Underglow + energy trail */}
      <ellipse cx="100" cy="104" rx={boost ? 96 : 84} ry={boost ? 14 : 10} fill={`url(#${id}-glow)`} opacity={0.85} />
      {boost > 0 && (
        <g opacity={boost === 2 ? 1 : 0.6}>
          <path d="M70 96 L62 120 H78 Z" fill={car.accent} opacity="0.7" filter={`url(#${id}-bloom)`} />
          <path d="M130 96 L122 120 H138 Z" fill={car.accent} opacity="0.7" filter={`url(#${id}-bloom)`} />
        </g>
      )}

      {/* Wheels / hover pods */}
      <rect x="14" y="74" width="28" height="22" rx="7" fill="#020617" />
      <rect x="158" y="74" width="28" height="22" rx="7" fill="#020617" />
      <rect x="16" y="88" width="24" height="3" rx="1.5" fill={car.accent} opacity="0.8" filter={`url(#${id}-bloom)`} />
      <rect
        x="160"
        y="88"
        width="24"
        height="3"
        rx="1.5"
        fill={car.accent}
        opacity="0.8"
        filter={`url(#${id}-bloom)`}
      />

      {/* Body */}
      <path d="M18 84 L30 52 Q100 34 170 52 L182 84 Q100 98 18 84 Z" fill={`url(#${id}-body)`} />
      <path d="M30 52 Q100 34 170 52 L166 58 Q100 42 34 58 Z" fill="white" opacity="0.12" />
      {/* Canopy */}
      <path
        d="M64 50 L80 28 H120 L136 50 Q100 44 64 50 Z"
        fill={`url(#${id}-glass)`}
        stroke={car.accent}
        strokeOpacity="0.5"
      />
      {/* Tail light bar */}
      <rect x="34" y="62" width="132" height="5" rx="2.5" fill={car.lights} filter={`url(#${id}-bloom)`} />
      <rect x="30" y="60" width="18" height="9" rx="3" fill={car.accent} filter={`url(#${id}-bloom)`} />
      <rect x="152" y="60" width="18" height="9" rx="3" fill={car.accent} filter={`url(#${id}-bloom)`} />
      {/* Diffuser + thrusters */}
      <path d="M52 78 H148 L140 90 H60 Z" fill="#020617" opacity="0.85" />
      {[74, 92, 108, 126].map((x) => (
        <rect key={x} x={x - 1} y="79" width="2" height="10" fill="#1e293b" />
      ))}
      <circle cx="70" cy="86" r={boost ? 6 : 4.5} fill={car.accent} filter={`url(#${id}-bloom)`} />
      <circle cx="130" cy="86" r={boost ? 6 : 4.5} fill={car.accent} filter={`url(#${id}-bloom)`} />

      {/* Rear wing */}
      {car.wing === "high" && (
        <g>
          <rect x="60" y="30" width="4" height="18" fill={car.bodyDark} />
          <rect x="136" y="30" width="4" height="18" fill={car.bodyDark} />
          <path d="M40 24 H160 L154 32 H46 Z" fill={`url(#${id}-body)`} />
          <rect x="44" y="24" width="112" height="2" fill={car.accent} opacity="0.9" />
        </g>
      )}
      {car.wing === "split" && (
        <g>
          <path d="M26 44 L58 38 L58 44 L30 50 Z" fill={`url(#${id}-body)`} />
          <path d="M174 44 L142 38 L142 44 L170 50 Z" fill={`url(#${id}-body)`} />
          <path d="M28 44 L58 38" stroke={car.accent} strokeWidth="1.5" />
          <path d="M172 44 L142 38" stroke={car.accent} strokeWidth="1.5" />
        </g>
      )}
    </svg>
  );
}

// ---------- Tracks ----------

export type TrackFeature = "skyline" | "tunnel" | "clouds" | "stadium";

export interface TrackTheme {
  id: string;
  name: string;
  description: string;
  sky: string;
  ground: string;
  road: string;
  rail: string;
  railAlt: string;
  glow: string;
  feature: TrackFeature;
}

export const TRACKS: TrackTheme[] = [
  {
    id: "neon-city",
    name: "Neon City",
    description: "Neon osmono'par binolar orasida",
    sky: "linear-gradient(180deg,#05010f 0%,#1a0b3d 55%,#3b0764 100%)",
    ground: "#05030d",
    road: "#0b0a18",
    rail: "#22d3ee",
    railAlt: "#e879f9",
    glow: "rgba(255,107,94,0.45)",
    feature: "skyline",
  },
  {
    id: "cyber-tunnel",
    name: "Cyber Tunnel",
    description: "Yorug' halqali yer osti tunneli",
    sky: "linear-gradient(180deg,#010806 0%,#022c22 60%,#064e3b 100%)",
    ground: "#010403",
    road: "#06110e",
    rail: "#34d399",
    railAlt: "#22d3ee",
    glow: "rgba(52,211,153,0.45)",
    feature: "tunnel",
  },
  {
    id: "sky-highway",
    name: "Sky Highway",
    description: "Bulutlar ustidagi tong trassasi",
    sky: "linear-gradient(180deg,#0f0a2e 0%,#4c1d95 45%,#db2777 80%,#fb923c 100%)",
    ground: "#1e1b4b",
    road: "#120f2e",
    rail: "#fbbf24",
    railAlt: "#f472b6",
    glow: "rgba(251,146,60,0.45)",
    feature: "clouds",
  },
  {
    id: "night-circuit",
    name: "Night Circuit",
    description: "Stadion chiroqlari ostidagi trek",
    sky: "linear-gradient(180deg,#000000 0%,#0b1530 70%,#1e3a8a 100%)",
    ground: "#020617",
    road: "#0a0f1c",
    rail: "#f8fafc",
    railAlt: "#ef4444",
    glow: "rgba(96,165,250,0.4)",
    feature: "stadium",
  },
];

export function trackById(id: string | null | undefined): TrackTheme {
  return TRACKS.find((track) => track.id === id) ?? TRACKS[0];
}

const TOWERS = [
  [0, 70],
  [26, 110],
  [48, 60],
  [70, 140],
  [96, 90],
  [120, 170],
  [146, 80],
  [170, 125],
  [196, 65],
  [220, 150],
  [246, 95],
  [268, 185],
  [296, 75],
  [320, 130],
  [346, 100],
  [370, 160],
  [396, 70],
];

/** The band of scenery on the horizon — scrolls sideways at the race's pace. */
export function TrackScenery({ track }: { track: TrackTheme }) {
  if (track.feature === "clouds") {
    return (
      <svg viewBox="0 0 400 200" preserveAspectRatio="none" className="h-full w-1/2 shrink-0">
        {[
          [20, 150, 70],
          [110, 165, 90],
          [220, 145, 80],
          [320, 160, 95],
        ].map(([x, y, w]) => (
          <ellipse key={x} cx={x + w / 2} cy={y} rx={w / 2} ry={16} fill="#fdf4ff" opacity="0.18" />
        ))}
        <path
          d="M0 200 L60 150 L110 175 L170 130 L240 170 L300 140 L360 165 L400 150 V200 Z"
          fill="#1e1b4b"
          opacity="0.8"
        />
      </svg>
    );
  }
  if (track.feature === "tunnel") {
    return (
      <svg viewBox="0 0 400 200" preserveAspectRatio="none" className="h-full w-1/2 shrink-0">
        {[0, 100, 200, 300].map((x) => (
          <g key={x}>
            <rect x={x} y="0" width="100" height="200" fill="#022c22" opacity="0.5" />
            <rect x={x + 46} y="0" width="8" height="200" fill={track.rail} opacity="0.25" />
            {[30, 80, 130].map((y) => (
              <rect key={y} x={x + 10} y={y} width="30" height="4" fill={track.railAlt} opacity="0.35" />
            ))}
          </g>
        ))}
      </svg>
    );
  }
  if (track.feature === "stadium") {
    return (
      <svg viewBox="0 0 400 200" preserveAspectRatio="none" className="h-full w-1/2 shrink-0">
        <path d="M0 200 V140 Q200 100 400 140 V200 Z" fill="#0b1220" />
        {[40, 140, 260, 360].map((x) => (
          <g key={x}>
            <rect x={x - 2} y="40" width="4" height="110" fill="#1e293b" />
            <rect x={x - 14} y="32" width="28" height="10" rx="2" fill="#e2e8f0" />
            <circle cx={x} cy="37" r="22" fill="#bfdbfe" opacity="0.12" />
          </g>
        ))}
        {Array.from({ length: 40 }, (_, i) => (
          <circle key={i} cx={(i * 10) % 400} cy={150 + (i % 3) * 8} r="1.3" fill="#94a3b8" opacity="0.5" />
        ))}
      </svg>
    );
  }
  // Neon City skyline with holographic billboards.
  return (
    <svg viewBox="0 0 400 200" preserveAspectRatio="none" className="h-full w-1/2 shrink-0">
      {TOWERS.map(([x, h], i) => (
        <g key={x}>
          <rect x={x} y={200 - h} width="22" height={h} fill={i % 2 ? "#0f0a24" : "#150d33"} />
          {Array.from({ length: Math.floor(h / 18) }, (_, k) => (
            <rect
              key={k}
              x={x + 4 + (k % 2) * 8}
              y={200 - h + 8 + k * 16}
              width="4"
              height="3"
              fill={k % 3 === 0 ? track.railAlt : track.rail}
              opacity="0.55"
            />
          ))}
        </g>
      ))}
      {[
        [60, 70, track.railAlt],
        [230, 50, track.rail],
      ].map(([x, y, color]) => (
        <g key={String(x)} opacity="0.75">
          <rect
            x={x as number}
            y={y as number}
            width="46"
            height="22"
            rx="3"
            fill="none"
            stroke={color as string}
            strokeWidth="1.5"
          />
          <rect x={(x as number) + 6} y={(y as number) + 7} width="26" height="3" fill={color as string} />
          <rect
            x={(x as number) + 6}
            y={(y as number) + 13}
            width="16"
            height="3"
            fill={color as string}
            opacity="0.6"
          />
        </g>
      ))}
    </svg>
  );
}
