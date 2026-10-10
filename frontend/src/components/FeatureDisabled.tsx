import { Lock } from "lucide-react";

/** Shown in place of a section the organization's client-config has closed. */
export function FeatureDisabled() {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col items-center gap-3 py-16 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
        <Lock size={22} />
      </span>
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
        Bu bo'lim yoqilmagan
      </h2>
      <p className="text-sm text-ink-muted">
        Bu bo'lim tashkilotingiz uchun yoqilmagan. Kerak bo'lsa, platforma
        ma'muriga murojaat qiling.
      </p>
    </div>
  );
}
