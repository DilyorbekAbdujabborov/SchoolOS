import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

/** The title row every non-dashboard page opens with — one place to keep
 * every page's heading, icon and optional subtitle/action visually
 * consistent instead of each page hand-rolling its own `<h1>`. */
export function PageHeader({
  icon: Icon,
  title,
  subtitle,
  action,
}: {
  icon?: LucideIcon;
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 className="flex items-center gap-2 text-xl font-bold text-slate-900 dark:text-slate-50">
          {Icon && <Icon className="text-brand-600 dark:text-brand-400" size={20} />}
          {title}
        </h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
