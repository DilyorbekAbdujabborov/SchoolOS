import logoMark from "../assets/logo-mark.png";

export function Logo({ subtitle }: { subtitle: string }) {
  return (
    <div className="flex items-center gap-3">
      <img src={logoMark} alt="" className="h-10 w-10 shrink-0" />
      <div className="min-w-0">
        <p className="truncate text-base font-bold leading-tight text-slate-900 dark:text-slate-50">
          School<span className="text-brand-500 dark:text-brand-400">OS</span>
        </p>
        <p className="truncate text-xs leading-tight text-slate-500 dark:text-slate-400">{subtitle}</p>
      </div>
    </div>
  );
}
