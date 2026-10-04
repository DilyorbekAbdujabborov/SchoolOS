import { TONE_STROKE, type Tone } from "../lib/tones";

/**
 * A radial progress ring. Drawn from the theme tokens so the track stays
 * invisible where it should be and the arc carries the tone.
 */
export function CircularProgress({
  value,
  size = 96,
  strokeWidth = 9,
  tone = "brand",
  /** Big number in the middle. Defaults to the rounded percentage. */
  children,
  caption,
}: {
  /** 0-100. Values outside that range are clamped. */
  value: number;
  size?: number;
  strokeWidth?: number;
  tone?: Tone;
  children?: React.ReactNode;
  caption?: string;
}) {
  const clamped = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div
      className="relative inline-flex shrink-0 items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          className="stroke-surface-sunken"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={`${TONE_STROKE[tone]} transition-[stroke-dashoffset] duration-700 ease-out`}
        />
      </svg>
      <div className="absolute flex flex-col items-center leading-none">
        {children ?? <span className="tabular text-xl font-bold text-ink">{Math.round(clamped)}%</span>}
        {caption && <span className="mt-1 text-[10px] font-medium text-ink-subtle">{caption}</span>}
      </div>
    </div>
  );
}

/**
 * A two-tone ring for completion counts: the remaining portion is drawn in a
 * second hue at low opacity, so a half-done ring reads as "half" at a glance
 * instead of as one undifferentiated arc.
 */
export function SegmentedRing({
  value,
  tone = "brand",
  restTone = "ember",
  size = 96,
  strokeWidth = 9,
  children,
}: {
  value: number;
  tone?: Tone;
  restTone?: Tone;
  size?: number;
  strokeWidth?: number;
  children?: React.ReactNode;
}) {
  const clamped = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div
      className="relative inline-flex shrink-0 items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          className={TONE_STROKE[restTone]}
          opacity={0.16}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - (clamped / 100) * circumference}
          className={`${TONE_STROKE[tone]} transition-[stroke-dashoffset] duration-700 ease-out`}
        />
      </svg>
      {children && <div className="absolute flex flex-col items-center leading-none">{children}</div>}
    </div>
  );
}
