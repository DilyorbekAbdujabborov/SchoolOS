import { Bell } from "lucide-react";
import { useEffect, useState } from "react";

import { isPushSubscribed, pushPermission, pushSupported, subscribeToPush } from "../lib/push";
import { PrimaryButton, SecondaryButton } from "./form";

/**
 * A soft, dismissable nudge to turn on browser push, shown globally at the
 * bottom of the app. It only appears for a logged-in user whose browser can do
 * push, who hasn't already subscribed, and who hasn't blocked the permission.
 * "Keyinroq" snoozes it for a week (localStorage), so it never nags; the
 * Notifications page keeps the full on/off toggle for deliberate changes.
 */

const DISMISS_KEY = "schoolos.pushPromptDismissed";
const COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000;

function recentlyDismissed(): boolean {
  try {
    const raw = localStorage.getItem(DISMISS_KEY);
    if (!raw) return false;
    const ts = Number(raw);
    return Number.isFinite(ts) && Date.now() - ts < COOLDOWN_MS;
  } catch {
    return false;
  }
}

export function PushPrompt() {
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!pushSupported() || pushPermission() === "denied" || recentlyDismissed()) return;

    let timer: ReturnType<typeof setTimeout> | undefined;
    let cancelled = false;
    isPushSubscribed()
      .then((subscribed) => {
        if (cancelled || subscribed) return;
        // Let the page settle before sliding the banner in.
        timer = setTimeout(() => setVisible(true), 1200);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  function dismiss() {
    try {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
    } catch {
      // Private mode / blocked storage: just hide for this session.
    }
    setVisible(false);
  }

  async function enable() {
    setBusy(true);
    try {
      await subscribeToPush();
    } finally {
      setBusy(false);
      // Granted or blocked, don't nag again straight away.
      dismiss();
    }
  }

  if (!visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 flex justify-center px-4 pb-4">
      <div className="flex w-full max-w-xl flex-col gap-3 rounded-2xl border border-line bg-surface p-4 shadow-xl sm:flex-row sm:items-center">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300">
          <Bell size={20} />
        </span>
        <p className="flex-1 text-sm text-slate-700 dark:text-slate-200">
          Bildirishnomalarni yoqing — yangi xabar va e'lonlardan telefoningizda xabardor bo'ling.
        </p>
        <div className="flex shrink-0 gap-2">
          <PrimaryButton onClick={enable} loading={busy}>
            Yoqish
          </PrimaryButton>
          <SecondaryButton onClick={dismiss}>Keyinroq</SecondaryButton>
        </div>
      </div>
    </div>
  );
}
