import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { TONE_CHIP, type Tone } from "../lib/tones";

/**
 * The title row every non-dashboard page opens with.
 *
 * The icon sits in a tone-tinted chip rather than being painted blue inline —
 * a page's accent comes from its subject (ember for gamification, emerald for
 * attendance, amber for planning), which is one small change that stops every
 * page header from looking identical and blue.
 */
export function PageHeader({
  icon: Icon,
  title,
  subtitle,
  action,
  tone = "brand",
}: {
  icon?: LucideIcon;
  title: string;
  subtitle?: string;
  action?: ReactNode;
  tone?: Tone;
}) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div className="flex min-w-0 items-center gap-3">
        {Icon && (
          <span
            className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${TONE_CHIP[tone]}`}
          >
            <Icon size={19} />
          </span>
        )}
        <div className="min-w-0">
          <h1 className="page-title truncate">{title}</h1>
          {subtitle && <p className="mt-0.5 text-sm text-ink-muted">{subtitle}</p>}
        </div>
      </div>
      {action && <div className="flex flex-wrap items-center gap-2">{action}</div>}
    </header>
  );
}
