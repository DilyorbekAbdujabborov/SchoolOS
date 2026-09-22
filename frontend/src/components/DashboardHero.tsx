import type { ReactNode } from "react";

import { Avatar } from "./Avatar";

type ChipTone = "slate" | "emerald" | "amber" | "brand" | "violet";

const CHIP_TONE_CLASS: Record<ChipTone, string> = {
  slate: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  emerald: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300",
  amber: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300",
  violet: "bg-violet-50 text-violet-700 dark:bg-violet-500/10 dark:text-violet-300",
};

interface HeroChip {
  label: string;
  tone?: ChipTone;
}

/** The welcome-banner card every role's dashboard opens with — avatar, greeting, context chips. */
export function DashboardHero({
  name,
  avatarSrc,
  subtitle,
  chips = [],
  action,
}: {
  name: string;
  avatarSrc?: string | null;
  subtitle: string;
  chips?: HeroChip[];
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center gap-4">
        <Avatar name={name} src={avatarSrc} size={56} />
        <div className="min-w-0">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">Salom, {name}!</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
          {chips.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {chips.map((chip) => (
                <span
                  key={chip.label}
                  className={`rounded-full px-3 py-1 text-xs font-medium ${CHIP_TONE_CLASS[chip.tone ?? "slate"]}`}
                >
                  {chip.label}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
      {action}
    </div>
  );
}
