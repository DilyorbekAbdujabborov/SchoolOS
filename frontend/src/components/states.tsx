import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { TONE_CHIP, TONE_DOT, type Tone } from "../lib/tones";

/**
 * Loading, empty, error and permission states.
 *
 * These used to be a line of grey text in the middle of a page. They now hold
 * the layout open (skeletons shaped like the content they replace) and give
 * empty states an icon, a headline and a next step, because an empty table in
 * a real product should say *why* it's empty, not just *that* it is.
 */

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function LoadingState({ label = "Yuklanmoqda..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-14" role="status" aria-live="polite">
      <span className="spinner h-5 w-5 text-ink-subtle" />
      <span className="text-sm text-ink-muted">{label}</span>
    </div>
  );
}

/** Skeleton grid used while a row of `StatCard`s is in flight. */
export function StatSkeletonGrid({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="card p-4 sm:p-5">
          <div className="flex items-start justify-between gap-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-8 w-8 rounded-lg" />
          </div>
          <Skeleton className="mt-3 h-6 w-16" />
        </div>
      ))}
    </div>
  );
}

/** Skeleton rows shaped like a table, so the page doesn't reflow on load. */
export function TableSkeleton({ rows = 5, cols = 3 }: { rows?: number; cols?: number }) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-line-soft bg-surface-raised px-4 py-3">
        <Skeleton className="h-3 w-28" />
      </div>
      {Array.from({ length: rows }, (_, r) => (
        <div
          key={r}
          className="flex items-center gap-4 border-b border-line-soft px-4 py-3.5 last:border-0"
        >
          {Array.from({ length: cols }, (_, c) => (
            <Skeleton key={c} className="h-3.5 flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}

/** Skeleton block for an arbitrary panel — pairs with a `LoadingState` label. */
export function PanelSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="card space-y-3 p-5" aria-hidden>
      <Skeleton className="h-4 w-1/3" />
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} className="h-3.5 w-full" />
      ))}
    </div>
  );
}

export function ErrorState({
  message = "Xatolik yuz berdi. Qayta urinib ko'ring.",
  action,
}: {
  message?: string;
  /** Usually a "Qayta urinish" button wired to the query's `refetch`. */
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center justify-center gap-2 border-rose-500/25 bg-rose-500/[0.06] px-6 py-10 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-500/12">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M12 8v5m0 3.5h.01M10.3 3.9 2.4 17.4A2 2 0 0 0 4.1 20.4h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"
            stroke="currentColor"
            strokeWidth="1.9"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-rose-600 dark:text-rose-400"
          />
        </svg>
      </span>
      <p className="text-sm font-medium text-ink">{message}</p>
      {action && <div className="mt-1">{action}</div>}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  icon: Icon,
  tone = "slate",
  action,
}: {
  title: string;
  description?: string;
  icon?: LucideIcon;
  tone?: Tone;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-line px-6 py-12 text-center">
      {Icon && (
        <span
          className={`mb-1 flex h-11 w-11 items-center justify-center rounded-xl ${TONE_CHIP[tone]}`}
        >
          <Icon size={20} />
        </span>
      )}
      <p className="text-sm font-semibold text-ink">{title}</p>
      {description && <p className="max-w-sm text-xs text-ink-subtle">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function PermissionDeniedState() {
  return (
    <div className="card flex flex-col items-center justify-center gap-2 border-amber-500/25 bg-amber-500/[0.06] px-6 py-12 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-500/12">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M12 3 4 6.5v5.2c0 4.6 3.2 8.3 8 9.3 4.8-1 8-4.7 8-9.3V6.5L12 3Z"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinejoin="round"
            className="text-amber-600 dark:text-amber-400"
          />
          <path
            d="M9.5 12.5 11 14l3.5-3.7"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-amber-600 dark:text-amber-400"
          />
        </svg>
      </span>
      <p className="text-sm font-semibold text-ink">Sizda bu bo'limni ko'rish huquqi yo'q</p>
      <p className="max-w-sm text-xs text-ink-subtle">
        Bu sahifa faqat tegishli rollar uchun ochiq. Savollaringiz bo'lsa, direktorga murojaat qiling.
      </p>
    </div>
  );
}

/** A compact "x ta natija" caption that sits above a list or table. */
export function ResultCount({ count, noun }: { count: number; noun: string }) {
  return (
    <p className="mb-3 text-xs text-ink-subtle">
      <span className="tabular font-semibold text-ink-muted">{count}</span> ta {noun}
    </p>
  );
}

/** Small inline legend used under charts. */
export function Legend({ items }: { items: { label: string; tone: Tone }[] }) {
  return (
    <ul className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1.5">
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-1.5 text-xs text-ink-muted">
          <span className={`h-2 w-2 rounded-full ${TONE_DOT[item.tone]}`} />
          {item.label}
        </li>
      ))}
    </ul>
  );
}
