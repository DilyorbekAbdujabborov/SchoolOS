import type { ReactNode } from "react";

import { TONE_CHIP, TONE_DOT, type Tone } from "../lib/tones";

/**
 * The status pill. One shape, one radius, one type size — colour is the only
 * variable, and it always means the same thing (see `lib/tones.ts`).
 */
export function Badge({
  tone = "slate",
  dot = false,
  className = "",
  children,
}: {
  tone?: Tone;
  /** A small solid dot before the label — reads faster in dense tables. */
  dot?: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <span className={`chip ${TONE_CHIP[tone]} ${className}`}>
      {dot && <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${TONE_DOT[tone]}`} />}
      {children}
    </span>
  );
}

/**
 * A status rendered without a background: coloured text plus a dot. Used in
 * dense contexts (table cells, inline stats) where a filled pill per row would
 * out-shout the data itself.
 */
export function StatusDot({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm font-medium text-ink">
      <span className={`h-2 w-2 shrink-0 rounded-full ${TONE_DOT[tone]}`} />
      {children}
    </span>
  );
}
