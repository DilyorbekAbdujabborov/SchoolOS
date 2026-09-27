import { TONE_BAR, TONE_TRACK, type Tone } from "../lib/tones";

export function ProgressBar({
  value,
  tone = "brand",
  size = "md",
  className = "",
}: {
  /** 0-100. Values outside that range are clamped. */
  value: number;
  tone?: Tone;
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  const clamped = Math.min(100, Math.max(0, value));
  const height = size === "sm" ? "h-1.5" : size === "lg" ? "h-3" : "h-2";

  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={`${height} w-full overflow-hidden rounded-full ${TONE_TRACK[tone]} ${className}`}
    >
      <div
        className={`h-full rounded-full ${TONE_BAR[tone]} transition-[width] duration-700 ease-out`}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
