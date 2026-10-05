import axios from "axios";

const ACCESS_KEY = "schoolos.access";
const REFRESH_KEY = "schoolos.refresh";

export const tokenStorage = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

/** Thrown when the backend returns 423 (student trying to use the platform during school hours). */
export class SchoolTimeLockedError extends Error {
  constructor(public detail: string) {
    super(detail);
    this.name = "SchoolTimeLockedError";
  }
}

/* ── App-wide School Time Lock ──────────────────────────────────────────────
   The lock is a *global* condition, not a per-request one: during school hours
   every gated endpoint answers 423, so if each query surfaced its own error the
   student would see a wall of "failed to load" messages. Instead any 423 flips
   one shared flag and the whole app shows the lock screen; the first 2xx from a
   gated endpoint (i.e. school is over) clears it again. */

type SchoolLockListener = (detail: string | null) => void;
const schoolLockListeners = new Set<SchoolLockListener>();
let schoolLockDetail: string | null = null;

/**
 * Subscribe to School Time Lock changes. The listener fires immediately with
 * the current state, then only on transitions (locked ↔ unlocked). Returns an
 * unsubscribe function.
 */
export function onSchoolTimeLock(listener: SchoolLockListener): () => void {
  schoolLockListeners.add(listener);
  listener(schoolLockDetail);
  return () => {
    schoolLockListeners.delete(listener);
  };
}

function setSchoolLock(detail: string | null): void {
  if (detail === schoolLockDetail) return;
  schoolLockDetail = detail;
  schoolLockListeners.forEach((listener) => listener(detail));
}

// Mirror of the backend's lock exemptions (SchoolTimeLockMiddleware): these
// endpoints answer even during the lock, so a 2xx from one of them tells us
// nothing about whether the lock has lifted — it must not clear the flag.
const LOCK_EXEMPT_PREFIXES = ["/auth/", "/schema", "/docs", "/redoc"];

function isLockExempt(url: string | undefined): boolean {
  if (!url) return false;
  const path = url.replace(/^https?:\/\/[^/]+/, "").replace(/^\/api/, "");
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return LOCK_EXEMPT_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

export const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const access = tokenStorage.getAccess();
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStorage.getRefresh();
  if (!refresh) return null;
  try {
    const { data } = await axios.post("/api/auth/refresh/", { refresh });
    // ROTATE_REFRESH_TOKENS is on, so the response carries a fresh refresh
    // token — store it, not the old one, so the chain keeps working if
    // blacklisting is ever enabled.
    tokenStorage.set(data.access, data.refresh ?? refresh);
    return data.access as string;
  } catch {
    tokenStorage.clear();
    return null;
  }
}

api.interceptors.response.use(
  (response) => {
    // A gated endpoint answering means school is over — lift the lock app-wide.
    // Exempt endpoints answer during the lock too, so they must not clear it.
    if (!isLockExempt(response.config?.url)) setSchoolLock(null);
    return response;
  },
  async (error) => {
    if (error.response?.status === 423) {
      const detail = error.response.data?.detail ?? "Locked";
      setSchoolLock(detail);
      return Promise.reject(new SchoolTimeLockedError(detail));
    }

    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      refreshInFlight ??= refreshAccessToken();
      const newAccess = await refreshInFlight;
      refreshInFlight = null;
      if (newAccess) {
        original.headers.Authorization = `Bearer ${newAccess}`;
        return api(original);
      }
    }

    return Promise.reject(error);
  },
);

/** The uniform error envelope the backend sends for every API error
 * (see apps/common/exceptions.py): { error_code, detail, errors }. */
export interface ApiError {
  /** Machine-readable code, e.g. "invalid", "permission_denied", "insufficient_xp". */
  errorCode: string;
  /** One human-readable message, always present — safe to show in a toast. */
  detail: string;
  /** Field-level validation errors, or null for a non-field error. */
  errors: Record<string, string[]> | null;
}

/**
 * Normalise anything thrown by axios into an {@link ApiError}. Reads the
 * backend envelope when present and falls back to a generic message for
 * network failures or non-DRF responses, so callers never have to poke at
 * `err.response.data` shapes themselves.
 */
export function getApiError(err: unknown): ApiError {
  const data = (err as { response?: { data?: unknown } })?.response?.data;
  if (data && typeof data === "object" && "detail" in data) {
    const body = data as { error_code?: string; detail?: unknown; errors?: unknown };
    return {
      errorCode: typeof body.error_code === "string" ? body.error_code : "error",
      detail: typeof body.detail === "string" ? body.detail : "Xatolik yuz berdi",
      errors: (body.errors as Record<string, string[]> | null) ?? null,
    };
  }
  return { errorCode: "error", detail: "Xatolik yuz berdi", errors: null };
}

const HANDOFF_COOKIE = "schoolos.handoff";

/** The base domain shared by every tenant — `<slug>.<base>` minus its first
 *  label. "toshloq-44.tochna.uz" -> "tochna.uz"; "tochna.uz" -> "tochna.uz". */
function baseDomainOf(host: string): string {
  const name = host.split(":")[0];
  const parts = name.split(".");
  return parts.length > 2 ? parts.slice(1).join(".") : name;
}

/** If the login happened on the main/apex host but the account lives on a
 *  tenant subdomain, move the session there. The tokens travel in a short-lived
 *  cookie scoped to the base domain (readable by the subdomain, never put in the
 *  URL, never sent to logs), and the browser does a full navigation.
 *  Returns true when a redirect was started — the caller must stop, the page is
 *  unloading. */
export function redirectToTenantHost(redirectTo: string | null | undefined): boolean {
  if (!redirectTo) return false;
  const { host, hostname } = window.location;
  if (redirectTo === host || redirectTo === hostname) return false;

  const base = redirectTo.split(".").slice(1).join(".");
  // Only move within the same base domain; never bounce a dev/other host off to
  // production because the API happened to compute a tenant host.
  if (!base || !(hostname === base || hostname.endsWith(`.${base}`))) return false;

  const access = tokenStorage.getAccess();
  const refresh = tokenStorage.getRefresh();
  if (access && refresh) {
    const value = encodeURIComponent(JSON.stringify({ a: access, r: refresh }));
    document.cookie =
      `${HANDOFF_COOKIE}=${value}; domain=${base}; path=/; max-age=60; secure; samesite=Lax`;
  }
  window.location.assign(`https://${redirectTo}/app`);
  return true;
}

/** On boot, adopt a session handed off from the main host (see
 *  redirectToTenantHost) and scrub the cookie. Safe to call unconditionally. */
export function absorbTenantHandoff(): void {
  const match = document.cookie.match(/(?:^|;\s*)schoolos\.handoff=([^;]+)/);
  const base = baseDomainOf(window.location.host);
  if (match) {
    try {
      const { a, r } = JSON.parse(decodeURIComponent(match[1]));
      if (a && r) tokenStorage.set(a, r);
    } catch {
      /* malformed handoff — ignore, just clear it below */
    }
    // One-time: delete on the base domain it was set on.
    document.cookie = `${HANDOFF_COOKIE}=; domain=${base}; path=/; max-age=0`;
  }
}

export async function login(
  email: string,
  password: string,
): Promise<{ redirecting: boolean }> {
  const { data } = await axios.post("/api/auth/login/", { email, password });
  tokenStorage.set(data.access, data.refresh);
  const redirecting = redirectToTenantHost(data.redirect_to);
  return { redirecting };
}

export function logout() {
  const refresh = tokenStorage.getRefresh();
  tokenStorage.clear();
  if (refresh) {
    // Fire-and-forget: blacklist the refresh token server-side so it can't be
    // reused. The UI logs out immediately regardless of the result.
    axios.post("/api/auth/logout/", { refresh }).catch(() => {});
  }
}
