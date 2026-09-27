import type { ReactNode } from "react";

import { TONE_DOT, TONE_RING, TONE_TEXT, type Tone } from "../lib/tones";
import { AvatarUploader } from "./AvatarUploader";
import { Badge } from "./Badge";

/**
 * The identity block every role's Profile page opens with.
 *
 * A wide accent edge plus an accent-tinted avatar ring give the profile a
 * recognisable "cover" without painting the whole panel — the stats strip
 * below sits on a raised well so the eye separates identity from numbers.
 */
export function ProfileHeaderCard({
  name,
  email,
  roleLabel,
  roleTone = "brand",
  stats,
  children,
}: {
  name: string;
  email: string | undefined;
  roleLabel: string;
  roleTone?: Tone;
  stats?: ReactNode;
  /** Role-specific extras rendered under the identity row (XP bar, etc.). */
  children?: ReactNode;
}) {
  return (
    <div className="card relative overflow-hidden">
      <span aria-hidden className={`absolute inset-x-0 top-0 h-1 ${TONE_DOT[roleTone]}`} />
      <div className="flex flex-col items-center gap-4 p-6 sm:flex-row sm:items-start">
        <span className={`rounded-full ring-2 ${TONE_RING[roleTone]}`}>
          <AvatarUploader />
        </span>
        <div className="min-w-0 flex-1 text-center sm:pt-2 sm:text-left">
          <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
            <h2 className="truncate text-xl font-bold tracking-tight text-ink">{name}</h2>
            <Badge tone={roleTone}>{roleLabel}</Badge>
          </div>
          <p className="mt-0.5 truncate text-sm text-ink-muted">{email}</p>
        </div>
      </div>

      {children}

      {stats && (
        <div className="grid grid-cols-2 gap-px border-t border-line-soft bg-line-soft sm:grid-cols-3">
          {stats}
        </div>
      )}
    </div>
  );
}

/** One cell of the stats strip — a number with a label, no card chrome. */
export function ProfileStat({
  label,
  value,
  tone = "slate",
}: {
  label: string;
  value: ReactNode;
  tone?: Tone;
}) {
  return (
    <div className="bg-surface px-4 py-3.5">
      <p className={`tabular text-xl font-bold leading-none ${TONE_TEXT[tone]}`}>{value}</p>
      <p className="mt-1.5 text-xs text-ink-subtle">{label}</p>
    </div>
  );
}
