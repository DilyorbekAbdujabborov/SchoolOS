import { useEffect, useState } from "react";

import {
  isPushSubscribed,
  pushPermission,
  pushSupported,
  subscribeToPush,
  unsubscribeFromPush,
} from "../lib/push";
import { PrimaryButton, SecondaryButton } from "./form";

/**
 * Opt-in control for browser push notifications. Reflects the live subscription
 * state, lets the user turn it on/off, and explains the two dead ends the user
 * can't fix from here: a browser that doesn't support push, and a permission the
 * user previously blocked (which only browser settings can reverse).
 */
export function PushToggle() {
  const supported = pushSupported();
  const [subscribed, setSubscribed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [blocked, setBlocked] = useState(false);

  useEffect(() => {
    if (!supported) return;
    setBlocked(pushPermission() === "denied");
    isPushSubscribed().then(setSubscribed).catch(() => setSubscribed(false));
  }, [supported]);

  async function handleEnable() {
    setBusy(true);
    setError(null);
    try {
      const ok = await subscribeToPush();
      setSubscribed(ok);
      if (!ok) {
        setBlocked(pushPermission() === "denied");
        setError("Bildirishnomalar yoqilmadi. Brauzer ruxsatini tekshiring.");
      }
    } catch {
      setError("Xatolik yuz berdi. Qayta urinib ko'ring.");
    } finally {
      setBusy(false);
    }
  }

  async function handleDisable() {
    setBusy(true);
    setError(null);
    try {
      await unsubscribeFromPush();
      setSubscribed(false);
    } catch {
      setError("O'chirishda xatolik yuz berdi.");
    } finally {
      setBusy(false);
    }
  }

  if (!supported) {
    return (
      <div className="card flex flex-col gap-1 p-4">
        <p className="font-medium text-slate-900 dark:text-slate-50">Brauzer bildirishnomalari</p>
        <p className="text-sm text-ink-muted">
          Bu brauzer push bildirishnomalarni qo'llab-quvvatlamaydi.
        </p>
      </div>
    );
  }

  return (
    <div className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        <p className="font-medium text-slate-900 dark:text-slate-50">Brauzer bildirishnomalari</p>
        <p className="text-sm text-ink-muted">
          {subscribed
            ? "Yoqilgan — yangi bildirishnomalar brauzeringizga keladi."
            : "Yangi bildirishnomalarni brauzer orqali oling."}
        </p>
        {blocked && !subscribed && (
          <p className="mt-1 text-sm text-amber-600 dark:text-amber-400">
            Ruxsat bloklangan. Brauzer sozlamalaridan sayt uchun bildirishnomaga ruxsat bering.
          </p>
        )}
        {error && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{error}</p>}
      </div>
      <div className="shrink-0">
        {subscribed ? (
          <SecondaryButton onClick={handleDisable} loading={busy}>
            O'chirish
          </SecondaryButton>
        ) : (
          <PrimaryButton onClick={handleEnable} loading={busy} disabled={blocked}>
            Yoqish
          </PrimaryButton>
        )}
      </div>
    </div>
  );
}
