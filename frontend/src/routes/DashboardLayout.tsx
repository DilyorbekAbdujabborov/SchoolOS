import type { LucideIcon } from "lucide-react";
import { Bell, ChevronDown, Flame, LogOut, Menu, Trophy, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { Avatar } from "../components/Avatar";
import { Logo } from "../components/Logo";
import { ThemeToggle } from "../components/ThemeToggle";
import { useAuth } from "../lib/auth";
import { todayLabel } from "../lib/schoolTime";
import { useStudentTopStats } from "../lib/useStudentTopStats";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** True for the dashboard/index link, so it isn't "active" on every sub-page too. */
  end?: boolean;
}

/** A labeled, collapsible group of nav items. Omit `label` for the top-level
 * items (e.g. the dashboard link) that sit above every group. */
export interface NavGroup {
  label?: string;
  items: NavItem[];
}

const ROLE_LABEL: Record<string, string> = {
  DIRECTOR: "Direktor",
  TEACHER: "O'qituvchi",
  STUDENT: "O'quvchi",
};

function NavLinkRow({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  return (
    <NavLink
      to={item.to}
      end={item.end}
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg border-l-2 px-3 py-2 text-sm font-medium transition-colors ${
          isActive
            ? "border-brand-600 bg-brand-50 text-brand-700 dark:border-brand-400 dark:bg-brand-500/10 dark:text-brand-300"
            : "hover-glow border-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-100"
        }`
      }
    >
      <item.icon size={17} className="shrink-0" />
      <span className="truncate">{item.label}</span>
    </NavLink>
  );
}

function NavSection({ group, onNavigate }: { group: NavGroup; onNavigate?: () => void }) {
  const [open, setOpen] = useState(true);

  if (!group.label) {
    return (
      <div className="space-y-1">
        {group.items.map((item) => (
          <NavLinkRow key={item.to} item={item} onNavigate={onNavigate} />
        ))}
      </div>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400 transition-colors hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
      >
        {group.label}
        <ChevronDown size={13} className={`transition-transform ${open ? "" : "-rotate-90"}`} />
      </button>
      {open && (
        <div className="mt-1 space-y-1">
          {group.items.map((item) => (
            <NavLinkRow key={item.to} item={item} onNavigate={onNavigate} />
          ))}
        </div>
      )}
    </div>
  );
}

function SidebarContent({ navGroups, brand, onNavigate }: { navGroups: NavGroup[]; brand: string; onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const displayName = user ? `${user.first_name || user.username} ${user.last_name || ""}`.trim() : "";

  return (
    <>
      <div className="border-b border-slate-200 px-5 py-5 dark:border-slate-800">
        <Logo subtitle={brand} />
      </div>
      <nav className="flex-1 space-y-4 overflow-y-auto px-3 py-4">
        {navGroups.map((group, i) => (
          <NavSection key={group.label ?? i} group={group} onNavigate={onNavigate} />
        ))}
      </nav>
      <div className="border-t border-slate-200 p-4 dark:border-slate-800">
        <div className="flex items-center gap-3">
          <Avatar name={displayName || "?"} src={user?.avatar_url} size={36} />
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100">{displayName}</p>
            <p className="text-xs text-slate-500 dark:text-slate-400">{user && ROLE_LABEL[user.role]}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-white/5"
        >
          <LogOut size={15} />
          Chiqish
        </button>
      </div>
    </>
  );
}

function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { user } = useAuth();
  const stats = useStudentTopStats();
  const notificationsPath = user ? `/${user.role.toLowerCase()}/notifications` : "/login";

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-4 py-3 backdrop-blur md:px-6 dark:border-slate-800 dark:bg-slate-950/80">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          aria-label="Menyuni ochish"
          className="rounded-md p-2 text-slate-600 hover:bg-slate-100 md:hidden dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <Menu size={20} />
        </button>
        <p className="text-lg font-bold text-brand-700 md:hidden dark:text-brand-400">SchoolOS</p>
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        {stats ? (
          <div className="hidden items-center gap-2 sm:flex">
            <span className="flex items-center gap-1.5 rounded-full bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-700 dark:bg-violet-500/10 dark:text-violet-300">
              {stats.level}-daraja
            </span>
            <span className="flex items-center gap-1.5 rounded-full bg-orange-50 px-3 py-1.5 text-xs font-semibold text-orange-700 dark:bg-orange-500/10 dark:text-orange-300">
              <Flame size={14} />
              {stats.currentStreak}
            </span>
            <span className="flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-semibold text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
              <Trophy size={14} />
              {stats.totalXp} XP
            </span>
          </div>
        ) : (
          <span className="hidden rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600 sm:inline dark:bg-slate-800 dark:text-slate-300">
            {todayLabel()}
          </span>
        )}
        <ThemeToggle />
        <NavLink
          to={notificationsPath}
          className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          aria-label="Bildirishnomalar"
        >
          <Bell size={17} />
        </NavLink>
      </div>
    </header>
  );
}

export function DashboardLayout({
  navGroups,
  brand,
  vibrant = false,
}: {
  navGroups: NavGroup[];
  brand: string;
  /** A livelier backdrop for the student experience — teacher/director stay neutral. */
  vibrant?: boolean;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Close the drawer whenever the route changes (covers back/forward nav too,
  // not just clicking a link — NavLink's own onClick wouldn't catch that).
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  return (
    <div
      className={`min-h-screen md:flex ${
        // A faint, single-hue brand wash for the student experience — kept
        // subtle so it reads as "livelier," not "a different color scheme."
        vibrant ? "bg-gradient-to-b from-brand-50/70 to-slate-50 dark:from-brand-900/20 dark:to-slate-950" : "bg-slate-50 dark:bg-slate-950"
      }`}
    >
      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            aria-label="Yopish"
            onClick={() => setMobileOpen(false)}
            className="absolute inset-0 bg-slate-900/40 dark:bg-black/60"
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-white shadow-sm dark:bg-slate-950">
            <div className="flex items-center justify-end px-3 pt-3">
              <button
                onClick={() => setMobileOpen(false)}
                aria-label="Yopish"
                className="rounded-md p-2 text-slate-400 hover:bg-slate-100 dark:text-slate-500 dark:hover:bg-white/5"
              >
                <X size={18} />
              </button>
            </div>
            <SidebarContent navGroups={navGroups} brand={brand} onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      {/* Desktop sidebar — follows the app theme: white + blue accent in light
          mode, near-black + blue accent in dark mode (never a mechanical
          inversion of the main content area, which sits one shade lighter). */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white md:flex dark:border-slate-800 dark:bg-slate-950">
        <SidebarContent navGroups={navGroups} brand={brand} />
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <TopBar onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
