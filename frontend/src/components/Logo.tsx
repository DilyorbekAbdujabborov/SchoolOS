import { GraduationCap } from "lucide-react";

export function Logo({ subtitle }: { subtitle: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-sm">
        <GraduationCap size={21} strokeWidth={2.25} />
      </span>
      <div className="min-w-0">
        <p className="truncate text-base font-bold leading-tight text-slate-900 dark:text-slate-50">SchoolOS</p>
        <p className="truncate text-xs leading-tight text-slate-500 dark:text-slate-400">{subtitle}</p>
      </div>
    </div>
  );
}
