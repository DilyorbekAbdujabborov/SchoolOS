import { ArrowRight, BookOpen, GraduationCap, ListChecks, Sparkles, Trophy, UserCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import logoMark from "../assets/logo-mark.png";
import { inputClass } from "../components/form";
import { ThemeToggle } from "../components/ThemeToggle";
import { useAuth } from "../lib/auth";

/**
 * The entry experience.
 *
 * A neutral charcoal panel, not a teal wall: the brand teal appears sparingly —
 * on the wordmark accent and the single primary action. The left panel carries
 * an abstract "learning graph" — a soft mesh, a plotted progress line and a
 * floating stat card — so the page reads as a product rather than a form with
 * a marketing panel bolted on, and it stays legible in both themes. A theme
 * toggle sits in the form panel so a visitor can switch before signing in.
 */

const FEATURES = [
  { icon: BookOpen, label: "Darslar, materiallar va topshiriqlar", tone: "text-brand-400" },
  { icon: ListChecks, label: "Testlar, o'zlashtirish va natijalar", tone: "text-ember-400" },
  { icon: UserCheck, label: "Davomat: keldi, kechikdi, kelmadi", tone: "text-emerald-400" },
  { icon: Trophy, label: "XP, reyting, yutuqlar va o'yinlar", tone: "text-amber-400" },
];

const ROLES = [
  { label: "Direktor", detail: "Maktab bo'yicha tahlil" },
  { label: "O'qituvchi", detail: "Sinflar, darslar, davomat" },
  { label: "O'quvchi", detail: "XP, reyting, yutuqlar" },
];

/** Decorative background: a soft mesh plus a plotted growth curve. */
function BrandBackdrop() {
  return (
    <svg
      aria-hidden
      className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.55]"
      preserveAspectRatio="xMidYMid slice"
      viewBox="0 0 600 800"
      fill="none"
    >
      <defs>
        <radialGradient id="glow-brand" cx="0" cy="0" r="1" gradientTransform="translate(150 120) rotate(38) scale(420 380)">
          <stop stopColor="#0eb39e" stopOpacity="0.30" />
          <stop offset="1" stopColor="#0eb39e" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="glow-ember" cx="0" cy="0" r="1" gradientTransform="translate(520 700) rotate(-40) scale(420 360)">
          <stop stopColor="#ff6b5e" stopOpacity="0.26" />
          <stop offset="1" stopColor="#ff6b5e" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="spark" x1="0" y1="0" x2="1" y2="0">
          <stop stopColor="#2fd3bc" stopOpacity="0.1" />
          <stop offset="0.5" stopColor="#2fd3bc" />
          <stop offset="1" stopColor="#ff6b5e" stopOpacity="0.15" />
        </linearGradient>
      </defs>

      <rect width="600" height="800" fill="url(#glow-brand)" />
      <rect width="600" height="800" fill="url(#glow-ember)" />

      {/* A faint grid — structure, not decoration. */}
      <g stroke="#ffffff" strokeOpacity="0.05">
        {Array.from({ length: 9 }, (_, i) => (
          <line key={`h${i}`} x1="0" y1={i * 100} x2="600" y2={i * 100} />
        ))}
        {Array.from({ length: 7 }, (_, i) => (
          <line key={`v${i}`} x1={i * 100} y1="0" x2={i * 100} y2="800" />
        ))}
      </g>

      {/* The "learning curve". */}
      <path
        d="M20 640 C 120 620, 150 540, 240 520 S 380 430, 440 360 S 520 230, 580 170"
        stroke="url(#spark)"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      {[
        [240, 520],
        [440, 360],
        [580, 170],
      ].map(([cx, cy], i) => (
        <g key={cx}>
          <circle cx={cx} cy={cy} r="16" fill="#2fd3bc" fillOpacity="0.12" />
          <circle cx={cx} cy={cy} r="4.5" fill="#6fe3ce" />
          {i === 2 && <circle cx={cx} cy={cy} r="4.5" fill="#ff6b5e" />}
        </g>
      ))}
    </svg>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (isSubmitting) return;
    setError(null);
    setIsSubmitting(true);
    try {
      const redirecting = await login(email, password);
      // On a cross-host handoff the browser is already navigating to the tenant
      // subdomain; routing here would just flash the dashboard on the wrong host.
      if (!redirecting) navigate("/app", { replace: true });
    } catch {
      setError("Login yoki parol noto'g'ri.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="relative min-h-screen bg-canvas">
      {/* Ambient wash behind the whole page — brand teal and ember, no purple. */}
      <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute -left-40 -top-40 h-[32rem] w-[32rem] rounded-full opacity-60 blur-3xl"
          style={{ background: "radial-gradient(circle, rgb(14 179 158 / 0.16), transparent 70%)" }}
        />
        <div
          className="absolute -bottom-52 -right-32 h-[30rem] w-[30rem] rounded-full opacity-50 blur-3xl"
          style={{ background: "radial-gradient(circle, rgb(255 107 94 / 0.14), transparent 70%)" }}
        />
      </div>

      <div className="relative flex min-h-screen items-center justify-center px-4 py-10 sm:px-6">
        <div className="w-full max-w-5xl overflow-hidden rounded-2xl border border-line bg-surface shadow-pop lg:grid lg:grid-cols-[1.05fr_1fr]">
          {/* ── Brand panel ───────────────────────────────────────────── */}
          <div className="relative flex flex-col justify-between overflow-hidden bg-slate-900 px-7 py-9 text-white sm:px-10 sm:py-11 dark:bg-[#0b0d13]">
            <BrandBackdrop />

            <div className="relative">
              <div className="flex items-center gap-3">
                <img src={logoMark} alt="" className="h-10 w-10 shrink-0" />
                <div>
                  <p className="text-lg font-bold leading-tight tracking-tight">SchoolOS</p>
                  <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-brand-400">
                    Maktab boshqaruvi
                  </p>
                </div>
              </div>

              <h1 className="mt-9 max-w-sm text-[26px] font-bold leading-[1.15] tracking-tight sm:text-[32px]">
                Maktabning butun raqamli yuzasi — bir joyda
              </h1>
              <p className="mt-3 max-w-sm text-sm leading-relaxed text-slate-300">
                Darslar, testlar, davomat, hisobotlar va gamifikatsiya. Direktor, o'qituvchi va
                o'quvchi uchun bitta platforma.
              </p>
            </div>

            <ul className="relative mt-9 space-y-3">
              {FEATURES.map(({ icon: Icon, label, tone }) => (
                <li key={label} className="flex items-center gap-3 text-[13px] text-slate-200">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/[0.07] ring-1 ring-inset ring-white/10">
                    <Icon size={15} className={tone} />
                  </span>
                  {label}
                </li>
              ))}
            </ul>

            {/* A concrete "what's inside" row rather than more marketing copy. */}
            <div className="relative mt-9 grid grid-cols-3 gap-px overflow-hidden rounded-xl bg-white/10">
              {ROLES.map((role) => (
                <div key={role.label} className="bg-slate-900/80 px-3 py-3 dark:bg-[#0b0d13]/80">
                  <p className="text-[13px] font-semibold">{role.label}</p>
                  <p className="mt-0.5 text-[11px] leading-tight text-slate-400">{role.detail}</p>
                </div>
              ))}
            </div>
          </div>

          {/* ── Form panel ────────────────────────────────────────────── */}
          <div className="flex flex-col justify-center px-7 py-9 sm:px-10 sm:py-11">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-brand-600 dark:text-brand-400">
                <Sparkles size={15} />
                <span className="text-[11px] font-semibold uppercase tracking-[0.12em]">
                  Xush kelibsiz
                </span>
              </div>
              <ThemeToggle />
            </div>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-ink">Tizimga kirish</h2>
            <p className="mt-1.5 text-sm text-ink-muted">
              Hisobingizga kirish uchun login va parolni kiriting.
            </p>

            <form onSubmit={handleSubmit} className="mt-7 space-y-4">
              <label className="block">
                <span className="mb-1.5 block text-sm font-medium text-ink-muted">Login</span>
                <input
                  type="email"
                  required
                  autoComplete="username"
                  autoFocus
                  placeholder="ism@school.uz"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClass}
                />
              </label>

              <label className="block">
                <span className="mb-1.5 block text-sm font-medium text-ink-muted">Parol</span>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    autoComplete="current-password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`${inputClass} pr-11`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-ink-subtle transition-colors hover:text-ink"
                    aria-label={showPassword ? "Parolni yashirish" : "Parolni ko'rsatish"}
                  >
                    {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                  </button>
                </div>
              </label>

              {error && (
                <p
                  role="alert"
                  className="pop rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300"
                >
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="btn btn-lg btn-primary group w-full"
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner" />
                    Kirilmoqda…
                  </>
                ) : (
                  <>
                    Kirish
                    <ArrowRight
                      size={17}
                      className="transition-transform duration-150 group-hover:translate-x-0.5"
                    />
                  </>
                )}
              </button>
            </form>

            <p className="mt-6 flex items-start gap-2 rounded-lg bg-surface-raised px-3 py-2.5 text-[11px] leading-relaxed text-ink-subtle">
              <GraduationCap size={14} className="mt-px shrink-0" />
              Hisobingizni direktor yoki administrator beradi. Parolni unutgan bo'lsangiz, maktab
              administratoriga murojaat qiling.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

/* Inline so the panel doesn't depend on the icon set's default sizing. */
function EyeIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M2.2 12S5.8 5.5 12 5.5 21.8 12 21.8 12 18.2 18.5 12 18.5 2.2 12 2.2 12Z"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M3 3l18 18M10.6 6.1A8.7 8.7 0 0 1 12 6c6.2 0 9.8 6 9.8 6a17 17 0 0 1-2.7 3.4M6.6 7.6C3.9 9.3 2.2 12 2.2 12s3.6 6 9.8 6a9.4 9.4 0 0 0 3.6-.7M9.9 9.9a3 3 0 0 0 4.2 4.2"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
