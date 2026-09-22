import { BookOpen, Eye, EyeOff, ListChecks, Trophy, UserCheck } from "lucide-react";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import logoMark from "../assets/logo-mark.png";
import { inputClass } from "../components/form";
import { useAuth } from "../lib/auth";

const FEATURES = [
  { icon: BookOpen, label: "Darslar va materiallar" },
  { icon: ListChecks, label: "Testlar va o'zlashtirish" },
  { icon: UserCheck, label: "Davomat va natijalar" },
  { icon: Trophy, label: "XP, yutuqlar va reyting" },
];

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
      await login(email, password);
      navigate("/", { replace: true });
    } catch {
      setError("Login yoki parol noto'g'ri.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10 dark:bg-slate-950">
      <div className="w-full max-w-4xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 md:grid md:grid-cols-2">
        <div className="flex flex-col justify-center gap-6 bg-slate-900 px-8 py-10 text-white sm:px-10 dark:bg-black">
          <div className="flex items-center gap-3">
            <img src={logoMark} alt="" className="h-11 w-11 shrink-0" />
            <p className="text-lg font-bold leading-tight">SchoolOS</p>
          </div>

          <div>
            <h1 className="text-2xl font-bold leading-tight sm:text-[28px]">
              Bilim olish shu yerdan boshlanadi
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-slate-300">
              Darslar, testlar, davomat va yutuqlar — barchasi bitta joyda. O'qituvchi, o'quvchi va
              direktor uchun yagona platforma.
            </p>
          </div>

          <ul className="space-y-3">
            {FEATURES.map(({ icon: Icon, label }) => (
              <li key={label} className="flex items-center gap-3 text-sm text-slate-200">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <Icon size={16} className="text-brand-400" />
                </span>
                {label}
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-col justify-center px-8 py-10 sm:px-10">
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-50">Tizimga kirish</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Login va parolingizni kiriting
          </p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
                Login
              </span>
              <input
                type="email"
                required
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className={inputClass}
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
                Parol
              </span>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`${inputClass} pr-10`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-slate-400 transition-colors hover:text-slate-600 dark:hover:text-slate-300"
                  aria-label={showPassword ? "Parolni yashirish" : "Parolni ko'rsatish"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </label>

            {error && (
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-400">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="hover-glow flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting && (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              )}
              {isSubmitting ? "Kirilmoqda..." : "Kirish"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
