import {
  ArrowRight,
  BarChart3,
  Bell,
  CalendarDays,
  Check,
  ClipboardCheck,
  FileText,
  Flame,
  Gamepad2,
  GraduationCap,
  Library,
  Lock,
  Shield,
  Sparkles,
  Swords,
  Trophy,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";

import logoMark from "../assets/logo-mark.png";
import { ThemeToggle } from "../components/ThemeToggle";

// Where "Bepul demo so'rash" points. Replace with the real SchoolOS contact.
const DEMO_URL = "https://t.me/sharqsoft";
const PHONE_DISPLAY = "+998 90 583 01 55";
const PHONE_HREF = "tel:+998905830155";

interface Feature {
  icon: LucideIcon;
  title: string;
  body: string;
}

const FEATURES: Feature[] = [
  { icon: ClipboardCheck, title: "Davomat", body: "Har dars uchun bir bosishda davomat, kechikish va sabab; avtomatik hisobot va eslatma." },
  { icon: CalendarDays, title: "Dars jadvali", body: "Sinf va o'qituvchi bo'yicha jadval, smenalar, darslarni avtomatik yaratish." },
  { icon: FileText, title: "Testlar va topshiriqlar", body: "Vaqt chegarali testlar, avtomatik baholash, fayl topshiriqlari." },
  { icon: Library, title: "Materiallar", body: "Fan bo'yicha fayl va havolalar kutubxonasi — o'qituvchi yuklaydi, o'quvchi ko'radi." },
  { icon: Trophy, title: "XP va liga", body: "9 pog'onali haftalik liga, XP, seriya va yutuqlar — o'qishni o'yinga aylantiradi." },
  { icon: Swords, title: "Duellar va o'yinlar", body: "Bilimga asoslangan duel va o'yinlar — mavzuni mustahkamlash uchun." },
  { icon: Bell, title: "Bildirishnomalar", body: "Telegram va brauzer orqali ota-ona va o'quvchiga bir zumda xabar." },
  { icon: BarChart3, title: "Hisobotlar", body: "Direktor uchun davomat, o'zlashtirish va faollik bo'yicha jonli statistika." },
];

interface Role {
  icon: LucideIcon;
  title: string;
  points: string[];
}

const ROLES: Role[] = [
  { icon: GraduationCap, title: "Direktor", points: ["Maktab bo'yicha jonli hisobot", "O'qituvchi va o'quvchi boshqaruvi", "Dars vaqti va bayram kunlari"] },
  { icon: Users, title: "O'qituvchi", points: ["Davomat va baholash", "Test, topshiriq, materiallar", "Sinf reytingi"] },
  { icon: Trophy, title: "O'quvchi", points: ["Darslar, testlar, materiallar", "XP, liga, duellar", "Shaxsiy o'sish va yutuqlar"] },
  { icon: Bell, title: "Ota-ona", points: ["Telegram orqali xabar", "Farzandi davomati", "Baho va natijalar"] },
];

function Nav() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-canvas/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
        <div className="flex items-center gap-2.5">
          <img src={logoMark} alt="" className="h-8 w-8 shrink-0" />
          <span className="text-lg font-bold text-ink">
            School<span className="text-brand-500 dark:text-brand-400">OS</span>
          </span>
        </div>
        <nav className="hidden items-center gap-7 text-sm font-medium text-ink-muted md:flex">
          <a href="#imkoniyatlar" className="transition-colors hover:text-ink">Imkoniyatlar</a>
          <a href="#rollar" className="transition-colors hover:text-ink">Rollar</a>
          <a href="#liga" className="transition-colors hover:text-ink">Liga</a>
        </nav>
        <div className="flex items-center gap-2 sm:gap-3">
          <ThemeToggle />
          <Link
            to="/login"
            className="rounded-lg px-3 py-2 text-sm font-semibold text-ink-muted transition-colors hover:bg-surface-raised hover:text-ink"
          >
            Kirish
          </Link>
          <a
            href={DEMO_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700"
          >
            Demo so'rash
          </a>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Ambient teal→ember glow. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          backgroundImage:
            "radial-gradient(60% 50% at 25% 0%, rgb(14 179 158 / 0.14) 0%, transparent 60%), radial-gradient(50% 45% at 90% 10%, rgb(255 107 94 / 0.12) 0%, transparent 55%)",
        }}
      />
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6 sm:py-28">
        <div className="mx-auto max-w-3xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-500/25 bg-brand-50/60 px-3 py-1 text-xs font-semibold text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
            <Sparkles size={13} />
            Maktab boshqaruvining raqamli platformasi
          </span>
          <h1 className="mt-6 text-4xl font-black leading-[1.05] tracking-tight text-ink sm:text-6xl">
            Butun maktab,{" "}
            <span className="bg-gradient-to-r from-brand-500 to-ember-500 bg-clip-text text-transparent">
              bitta tizim
            </span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-ink-muted">
            Davomat, dars jadvali, testlar, materiallar va hisobotlar — hammasi bir joyda.
            O'quvchilarni XP va haftalik liga bilan rag'batlantiring, ota-onalarni Telegram orqali xabardor qiling.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a
              href={DEMO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 sm:w-auto"
            >
              Bepul demo so'rash
              <ArrowRight size={17} />
            </a>
            <Link
              to="/login"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-line-strong bg-surface px-6 py-3 text-sm font-semibold text-ink transition-colors hover:bg-surface-raised sm:w-auto"
            >
              Tizimga kirish
            </Link>
          </div>
        </div>

        {/* Floating stat cards — a glimpse of the product. */}
        <div className="mx-auto mt-16 grid max-w-4xl grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
          {[
            { icon: ClipboardCheck, label: "Davomat", value: "98%", tone: "brand" as const },
            { icon: Trophy, label: "Haftalik liga", value: "Oltin", tone: "ember" as const },
            { icon: Flame, label: "Seriya", value: "14 kun", tone: "amber" as const },
            { icon: BarChart3, label: "O'zlashtirish", value: "87%", tone: "brand" as const },
          ].map((s) => {
            const tones = {
              brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300",
              ember: "bg-ember-50 text-ember-700 dark:bg-ember-500/10 dark:text-ember-300",
              amber: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
            };
            return (
              <div key={s.label} className="rounded-2xl border border-line bg-surface p-4 shadow-card">
                <span className={`inline-flex h-9 w-9 items-center justify-center rounded-xl ${tones[s.tone]}`}>
                  <s.icon size={18} />
                </span>
                <p className="mt-3 text-2xl font-bold text-ink">{s.value}</p>
                <p className="text-xs text-ink-subtle">{s.label}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Features() {
  return (
    <section id="imkoniyatlar" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">Bitta platforma, hamma kerakli narsa</h2>
        <p className="mt-3 text-ink-muted">Qog'oz jurnal va qo'lda hisob-kitob o'rniga — avtomatlashtirilgan, aniq va zamonaviy tizim.</p>
      </div>
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-2xl border border-line bg-surface p-5 transition-shadow hover:shadow-card">
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400">
              <f.icon size={21} />
            </span>
            <h3 className="mt-4 font-semibold text-ink">{f.title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function LigaHighlight() {
  return (
    <section id="liga" className="relative overflow-hidden border-y border-line bg-surface">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{ backgroundImage: "radial-gradient(50% 60% at 80% 50%, rgb(255 107 94 / 0.1) 0%, transparent 60%)" }}
      />
      <div className="mx-auto grid max-w-6xl items-center gap-10 px-4 py-20 sm:px-6 lg:grid-cols-2">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full bg-ember-50 px-3 py-1 text-xs font-semibold text-ember-700 dark:bg-ember-500/10 dark:text-ember-300">
            <Shield size={13} />
            Gamifikatsiya
          </span>
          <h2 className="mt-5 text-3xl font-bold tracking-tight text-ink sm:text-4xl">
            O'qish — o'yin kabi qiziqarli
          </h2>
          <p className="mt-4 text-ink-muted">
            Har hafta o'quvchilar XP to'plab ligada yuqoriga ko'tariladi: Bronzadan Afsonaga qadar 9 pog'ona.
            Duellar, o'yinlar, seriya va yutuqlar — motivatsiya o'z-o'zidan oshadi.
          </p>
          <ul className="mt-6 space-y-2.5">
            {["9 pog'onali haftalik liga", "XP, seriya va yutuqlar", "Duel va bilim o'yinlari", "Sinf va umumiy reyting"].map((t) => (
              <li key={t} className="flex items-center gap-2.5 text-sm text-ink">
                <span className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand-500/15 text-brand-600 dark:text-brand-400">
                  <Check size={13} />
                </span>
                {t}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-line bg-canvas p-5 shadow-card">
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-subtle">Oltin liga · shu hafta</p>
          <div className="mt-4 space-y-2">
            {[
              { rank: 1, name: "Valibek A.", xp: 1240, tone: "amber" },
              { rank: 2, name: "Dilnoza M.", xp: 1180, tone: "slate" },
              { rank: 3, name: "Jasur K.", xp: 1095, tone: "ember" },
            ].map((r) => (
              <div key={r.rank} className="flex items-center gap-3 rounded-xl border border-line bg-surface px-3 py-2.5">
                <span
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white ${
                    r.tone === "amber" ? "bg-amber-500" : r.tone === "ember" ? "bg-ember-500" : "bg-slate-400 dark:bg-slate-600"
                  }`}
                >
                  {r.rank}
                </span>
                <span className="flex-1 text-sm font-medium text-ink">{r.name}</span>
                <span className="inline-flex items-center gap-1 text-sm font-semibold text-brand-600 dark:text-brand-400">
                  <Trophy size={13} />
                  {r.xp}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center justify-between rounded-xl bg-brand-500/10 px-3 py-2.5 text-sm">
            <span className="flex items-center gap-2 font-medium text-brand-700 dark:text-brand-300">
              <Gamepad2 size={15} /> Keyingi duel
            </span>
            <span className="font-semibold text-ink">+25 XP</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function Roles() {
  return (
    <section id="rollar" className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
      <div className="mx-auto max-w-2xl text-center">
        <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">Har kim uchun o'z paneli</h2>
        <p className="mt-3 text-ink-muted">Direktor, o'qituvchi, o'quvchi va ota-ona — har biri kerakli ma'lumotni ko'radi.</p>
      </div>
      <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {ROLES.map((r) => (
          <div key={r.title} className="rounded-2xl border border-line bg-surface p-5">
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-ember-500/10 text-ember-600 dark:text-ember-400">
              <r.icon size={21} />
            </span>
            <h3 className="mt-4 font-semibold text-ink">{r.title}</h3>
            <ul className="mt-3 space-y-2">
              {r.points.map((p) => (
                <li key={p} className="flex items-start gap-2 text-sm text-ink-muted">
                  <Check size={15} className="mt-0.5 shrink-0 text-brand-500" />
                  {p}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}

function SecurityStrip() {
  return (
    <section className="mx-auto max-w-6xl px-4 pb-4 sm:px-6">
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-line bg-surface px-6 py-6 text-center sm:flex-row sm:justify-center sm:gap-8 sm:text-left">
        <span className="inline-flex items-center gap-2 text-sm font-medium text-ink">
          <Lock size={16} className="text-brand-600 dark:text-brand-400" /> Dars vaqti qulfi
        </span>
        <span className="inline-flex items-center gap-2 text-sm font-medium text-ink">
          <Shield size={16} className="text-brand-600 dark:text-brand-400" /> Rolga asoslangan ruxsat
        </span>
        <span className="inline-flex items-center gap-2 text-sm font-medium text-ink">
          <Bell size={16} className="text-brand-600 dark:text-brand-400" /> Telegram xabarlar
        </span>
        <span className="inline-flex items-center gap-2 text-sm font-medium text-ink">
          <GraduationCap size={16} className="text-brand-600 dark:text-brand-400" /> O'zbek tilida
        </span>
      </div>
    </section>
  );
}

function CtaBanner() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
      <div className="relative overflow-hidden rounded-3xl border border-brand-500/20 bg-gradient-to-br from-brand-600 to-brand-700 px-6 py-14 text-center sm:px-10">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{ backgroundImage: "radial-gradient(40% 60% at 85% 20%, rgb(255 107 94 / 0.35) 0%, transparent 60%)" }}
        />
        <div className="relative">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Maktabingizni raqamlashtiring</h2>
          <p className="mx-auto mt-3 max-w-xl text-white/85">
            Bepul demo so'rang — tizimni maktabingiz ma'lumotlari bilan ko'rsatamiz va bosqichma-bosqich joriy etamiz.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a
              href={DEMO_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-brand-700 shadow-sm transition-transform hover:scale-[1.02] sm:w-auto"
            >
              Bepul demo so'rash
              <ArrowRight size={17} />
            </a>
            <a
              href={PHONE_HREF}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/30 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10 sm:w-auto"
            >
              {PHONE_DISPLAY}
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6">
        <div className="flex items-center gap-2.5">
          <img src={logoMark} alt="" className="h-7 w-7" />
          <span className="font-bold text-ink">
            School<span className="text-brand-500 dark:text-brand-400">OS</span>
          </span>
          <span className="ml-2 text-sm text-ink-subtle">Butun maktab, bitta tizim.</span>
        </div>
        <div className="flex items-center gap-5 text-sm text-ink-muted">
          <Link to="/login" className="transition-colors hover:text-ink">Kirish</Link>
          <a href={DEMO_URL} target="_blank" rel="noopener noreferrer" className="transition-colors hover:text-ink">Demo</a>
          <a href={PHONE_HREF} className="transition-colors hover:text-ink">{PHONE_DISPLAY}</a>
        </div>
      </div>
      <p className="pb-6 text-center text-xs text-ink-subtle">© {new Date().getFullYear()} SchoolOS</p>
    </footer>
  );
}

export function LandingPage() {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <Nav />
      <main>
        <Hero />
        <SecurityStrip />
        <Features />
        <LigaHighlight />
        <Roles />
        <CtaBanner />
      </main>
      <Footer />
    </div>
  );
}
