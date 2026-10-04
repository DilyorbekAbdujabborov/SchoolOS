import { Lock, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "../lib/api";

/**
 * Full-screen notice shown to a student who opens the app during school hours.
 * It owns its own way back in: a gated endpoint is pinged on an interval (and
 * on demand), and the first 2xx — i.e. the moment the lock lifts — clears the
 * app-wide lock through the api interceptor, so the student never has to reload.
 */
export function SchoolTimeLockScreen({ message }: { message: string }) {
  const [checking, setChecking] = useState(false);

  async function recheck() {
    setChecking(true);
    try {
      // Any gated endpoint will do: a 2xx tells the interceptor the lock is over
      // and flips the whole app back on; a 423 just re-arms this screen.
      await api.get("/streaks/me/");
    } catch {
      // Still locked (or offline) — the screen stays up.
    } finally {
      setChecking(false);
    }
  }

  useEffect(() => {
    const id = setInterval(recheck, 60_000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex min-h-screen select-none flex-col items-center justify-center gap-5 bg-slate-900 px-6 text-center text-white">
      <Lock className="h-16 w-16 text-slate-400" strokeWidth={1.5} />
      <h1 className="text-2xl font-bold">HOZIR DARS VAQTI</h1>
      <p className="max-w-md text-slate-300">{message}</p>
      <button
        onClick={recheck}
        disabled={checking}
        className="mt-1 inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-700 disabled:opacity-60"
      >
        <RefreshCw size={15} className={checking ? "animate-spin" : undefined} />
        {checking ? "Tekshirilmoqda..." : "Qayta urinish"}
      </button>
    </div>
  );
}
