import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Avatar } from "./Avatar";
import { TONE_CHIP, TONE_DOT, type Tone } from "../lib/tones";

type HeroChip = { label: string; tone?: Tone; icon?: LucideIcon };

/**
 * The welcome banner every role's dashboard opens with.
 *
 * Deliberately *not* a coloured or gradient panel: it's a neutral card with
 * one narrow accent edge, so the hero establishes the page's title hierarchy
 * without spending the brand colour on the largest element on screen. The
 * accent edge takes a per-role tone, which is the first signal that the
 * director, teacher and student experiences are different products sharing one
 * system.
 */
export function DashboardHero({
  name,
  avatarSrc,
  subtitle,
  chips = [],
  action,
  tone = "brand",
  greeting,
}: {
  name: string;
  avatarSrc?: string | null;
  subtitle: string;
  chips?: HeroChip[];
  action?: ReactNode;
  tone?: Tone;
  /** Overrides the default "Salom, …!" opener (directors get a formal one). */
  greeting?: string;
}) {
  return (
    <div className="card relative overflow-hidden p-5 sm:p-6">
      <span aria-hidden className={`absolute inset-y-0 left-0 w-1 ${TONE_DOT[tone]}`} />
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-w-0 items-center gap-4">
          <Avatar name={name} src={avatarSrc} size={56} />
          <div className="min-w-0">
            <h1 className="page-title">
              {greeting ?? "Salom"}<span className="text-ink-muted">, {name}!</span>
            </h1>
            <p className="mt-1 text-sm text-ink-muted">{subtitle}</p>
            {chips.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {chips.map((chip) => (
                  <span key={chip.label} className={`chip ${TONE_CHIP[chip.tone ?? "slate"]}`}>
                    {chip.icon && <chip.icon size={12} />}
                    {chip.label}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        {action && <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div>}
      </div>
    </div>
  );
}
