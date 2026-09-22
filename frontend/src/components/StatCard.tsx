import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

type StatCardTone = "brand" | "amber" | "emerald" | "violet" | "rose";

const ICON_TONE_CLASS: Record<StatCardTone, string> = {
  brand: "bg-brand-50 text-brand-600 dark:bg-brand-500/10 dark:text-brand-300",
  amber: "bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-300",
  emerald: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300",
  violet: "bg-violet-50 text-violet-600 dark:bg-violet-500/10 dark:text-violet-300",
  rose: "bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-300",
};

interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  /** When set, the whole card becomes a link — for stats that lead somewhere. */
  to?: string;
  /** When set instead of `to`, the card becomes a button — for stats that
   * drill down in place (e.g. expanding a list) rather than navigating. */
  onClick?: () => void;
  icon?: LucideIcon;
  tone?: StatCardTone;
}

export function StatCard({ label, value, hint, to, onClick, icon: Icon, tone = "brand" }: StatCardProps) {
  const interactive = Boolean(to || onClick);
  const className = `${interactive ? "hover-card" : ""} rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm dark:border-slate-800 dark:bg-slate-900`;

  const content = (
    <>
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        {Icon && (
          <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${ICON_TONE_CLASS[tone]}`}>
            <Icon size={18} />
          </span>
        )}
      </div>
      <p className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-50">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{hint}</p>}
    </>
  );

  if (to) {
    return (
      <Link to={to} className={className}>
        {content}
      </Link>
    );
  }

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={`w-full ${className}`}>
        {content}
      </button>
    );
  }

  return <div className={className}>{content}</div>;
}
