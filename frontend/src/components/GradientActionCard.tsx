import type { LucideIcon } from "lucide-react";
import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

import { TONE_FILL, type Tone } from "../lib/tones";

/**
 * The one high-emphasis call to action per view.
 *
 * A solid fill is expensive in a design system, so it is spent here: on the
 * single thing the view wants the user to do next (clear today's attendance,
 * sit an open test). Its tone carries the meaning — amber when the action is
 * overdue, brand when it's simply the main path. Everything else on the page
 * stays neutral, which is what makes this card read as the primary action
 * instead of one more coloured rectangle.
 */
export function GradientActionCard({
  icon: Icon,
  title,
  subtitle,
  to,
  tone = "brand",
}: {
  icon: LucideIcon;
  title: string;
  subtitle: string;
  to: string;
  tone?: Tone;
}) {
  return (
    <Link
      to={to}
      className={`group flex items-center justify-between gap-4 rounded-2xl p-5 text-white shadow-raise transition-transform duration-150 hover:-translate-y-0.5 ${TONE_FILL[tone]}`}
    >
      <div className="flex items-center gap-4">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white/15 ring-1 ring-inset ring-white/20">
          <Icon size={21} />
        </span>
        <div className="min-w-0">
          <p className="font-semibold tracking-tight">{title}</p>
          <p className="text-sm text-white/75">{subtitle}</p>
        </div>
      </div>
      <ArrowRight
        size={19}
        className="shrink-0 text-white/70 transition-transform duration-150 group-hover:translate-x-0.5"
      />
    </Link>
  );
}
