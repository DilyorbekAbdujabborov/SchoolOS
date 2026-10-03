import { api } from "./api";

/**
 * Web Push client: registers the service worker, negotiates a subscription with
 * the browser's PushManager using the server's VAPID public key, and mirrors it
 * to the backend so `notify()` can reach this device. Every entry point is
 * guarded by `pushSupported()` so unsupported browsers (e.g. iOS before 16.4, or
 * a non-secure origin) degrade quietly.
 */

const SW_URL = "/sw.js";

export function pushSupported(): boolean {
  return (
    "serviceWorker" in navigator &&
    "PushManager" in window &&
    "Notification" in window
  );
}

/** The browser stores its permission decision; "default" means not yet asked. */
export function pushPermission(): NotificationPermission {
  return pushSupported() ? Notification.permission : "denied";
}

/** VAPID keys arrive base64url-encoded; PushManager wants a raw byte array. */
function urlBase64ToUint8Array(base64String: string): BufferSource {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  const buffer = new ArrayBuffer(raw.length);
  const output = new Uint8Array(buffer);
  for (let i = 0; i < raw.length; i += 1) {
    output[i] = raw.charCodeAt(i);
  }
  return output;
}

async function getRegistration(): Promise<ServiceWorkerRegistration> {
  const existing = await navigator.serviceWorker.getRegistration(SW_URL);
  if (existing) return existing;
  return navigator.serviceWorker.register(SW_URL);
}

export async function isPushSubscribed(): Promise<boolean> {
  if (!pushSupported()) return false;
  const registration = await navigator.serviceWorker.getRegistration(SW_URL);
  const subscription = await registration?.pushManager.getSubscription();
  return Boolean(subscription);
}

/**
 * Asks for permission (if needed), subscribes, and registers the endpoint with
 * the backend. Returns false when the browser can't or the user declines, so the
 * caller can keep the toggle off without treating it as an error.
 */
export async function subscribeToPush(): Promise<boolean> {
  if (!pushSupported()) return false;

  const permission = await Notification.requestPermission();
  if (permission !== "granted") return false;

  const registration = await getRegistration();
  await navigator.serviceWorker.ready;

  const { data } = await api.get<{ public_key: string }>("/push/vapid-key/");
  if (!data.public_key) return false;

  const existing = await registration.pushManager.getSubscription();
  const subscription =
    existing ??
    (await registration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(data.public_key),
    }));

  await api.post("/push/subscribe/", subscription.toJSON());
  return true;
}

/** Tears down the local subscription and tells the backend to forget it. */
export async function unsubscribeFromPush(): Promise<void> {
  if (!pushSupported()) return;
  const registration = await navigator.serviceWorker.getRegistration(SW_URL);
  const subscription = await registration?.pushManager.getSubscription();
  if (!subscription) return;

  try {
    await api.post("/push/unsubscribe/", { endpoint: subscription.endpoint });
  } finally {
    await subscription.unsubscribe();
  }
}
