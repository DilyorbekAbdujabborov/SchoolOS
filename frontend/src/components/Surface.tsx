import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { TONE_CARD, TONE_DOT, type Tone } from "../lib/tones";

/**
 * The card primitive.
 *
 * Every panel in the app is one of three recipes, and choosing between them is
 * the main way visual hierarchy is expressed:
 *
 *   `<Card>`       neutral surface, hairline, soft shadow — the default
 *   `<Card tone>`  the same card with a faint single-hue wash, for a card
 *                  whose entire subject is one status (a streak, a leader,
 *                  an alert). Never as decoration.
 *   `<Card inset>` recessed well for a table, a list, or anything that needs
 *                  to read as "inside" the card rather than beside it.
 *
 * `interactive` adds the app's one hover treatment: a small lift plus an
 * accent-tinted border. `accent` draws a 3px edge on the leading side instead,
 * which is the lightest possible way to tag a card with a category.
 */
export function Card({
  children,
  className = "",
  tone,
  inset = false,
  interactive = false,
  accent,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  tone?: Tone;
  inset?: boolean;
  interactive?: boolean;
  accent?: Tone;
  as?: "div" | "section" | "article" | "aside";
}) {
  const surface = tone ? TONE_CARD[tone] : inset ? "bg-surface-raised" : "card";
  return (
    <Tag
      className={`${surface} ${interactive ? "hover-card" : ""} ${
        accent ? "relative overflow-hidden border-l-[3px]" : ""
      } ${className}`}
    >
      {accent && (
        <span
          aria-hidden
          className={`absolute inset-y-0 left-0 w-[3px] ${TONE_DOT[accent]}`}
        />
      )}
      {children}
    </Tag>
  );
}

/** A card that navigates — the `<Link>` counterpart of `Card interactive`. */
export function CardLink({
  to,
  children,
  className = "",
  tone,
  accent,
}: {
  to: string;
  children: ReactNode;
  className?: string;
  tone?: Tone;
  accent?: Tone;
}) {
  return (
    <Link
      to={to}
      className={`${tone ? TONE_CARD[tone] : "card"} hover-card relative overflow-hidden ${
        accent ? "border-l-[3px]" : ""
      } ${className}`}
    >
      {accent && <span aria-hidden className={`absolute inset-y-0 left-0 w-[3px] ${TONE_DOT[accent]}`} />}
      {children}
    </Link>
  );
}

/**
 * The section wrapper every page composes with: an optional heading with a
 * short uppercase eyebrow, an optional "see all" link, then content. This
 * replaces the hand-copied `<h2 className="mb-3 text-sm font-semibold …">`
 * pattern that had drifted across ~40 call sites.
 */
export function Section({
  title,
  eyebrow,
  icon: Icon,
  iconTone = "brand",
  action,
  children,
  className = "",
  bodyClassName = "",
}: {
  title?: string;
  eyebrow?: string;
  icon?: LucideIcon;
  iconTone?: Tone;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={className}>
      {(title || action) && (
        <header className="mb-3 flex items-end justify-between gap-3">
          <div className="min-w-0">
            {eyebrow && <p className="section-eyebrow mb-1">{eyebrow}</p>}
            {title && (
              <h2 className="section-title flex items-center gap-2">
                {Icon && <Icon size={16} className={TONE_DOT[iconTone]} />}
                {title}
              </h2>
            )}
          </div>
          {action}
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
    </section>
  );
}

/** The "Batafsil →" affordance that ends a section header. */
export function SectionLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="link-more shrink-0">
      {children}
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden className="-mr-0.5">
        <path
          d="m9 18 6-6-6-6"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </Link>
  );
}

/** A small titled block inside a card — used where a plain bold line is too flat. */
export function CardTitle({
  icon: Icon,
  tone = "brand",
  className = "",
  children,
  action,
}: {
  icon?: LucideIcon;
  tone?: Tone;
  className?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className={`mb-3 flex items-center justify-between gap-2 ${className}`}>
      <h3 className="flex items-center gap-2 text-sm font-semibold text-ink">
        {Icon && <Icon size={16} className={TONE_DOT[tone]} />}
        {children}
      </h3>
      {action}
    </div>
  );
}
