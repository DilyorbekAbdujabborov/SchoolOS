import type { LucideIcon } from "lucide-react";
import { Bell, ChevronsLeft, ChevronsRight, Flame, Gauge, LogOut, Menu, Trophy, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import logoMark from "../assets/logo-mark.png";
import { Avatar } from "../components/Avatar";
import { PushPrompt } from "../components/PushPrompt";
import { ThemeToggle } from "../components/ThemeToggle";
import { useAuth } from "../lib/auth";
import { useStudentTopStats } from "../lib/useStudentTopStats";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  /** True for the dashboard/index link, so it isn't "active" on every sub-page too. */
  end?: boolean;
}

export interface NavGroup {
  label?: string;
  items: NavItem[];
}

const ROLE_LABEL: Record<string, string> = {
  DIRECTOR: "Direktor",
  TEACHER: "O'qituvchi",
  STUDENT: "O'quvchi",
};

/** Remembered across sessions so the sidebar keeps the width the user chose. */
const SIDEBAR_KEY = "schoolos.sidebar.collapsed";

function BrandHeader({ brand, collapsed }: { brand: string; collapsed: boolean }) {
  return (
    <div
      className={`flex select-none items-center border-b border-slate-200 dark:border-slate-800 ${
        collapsed ? "justify-center px-2 py-4" : "gap-3 px-5 py-4"
      }`}
    >
      <img src={logoMark} alt="" className="h-9 w-9 shrink-0" />
      {!collapsed && (
        <div className="min-w-0">
          <p className="truncate text-base font-bold leading-tight text-slate-900 dark:text-slate-50">
            School<span className="text-brand-500 dark:text-brand-400">OS</span>
          </p>
          <p className="truncate text-xs leading-tight text-slate-500 dark:text-slate-400">{brand}</p>
        </div>
      )}
    </div>
  );
}

function SidebarNav({
  groups,
  collapsed,
  onNavigate,
}: {
  groups: NavGroup[];
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex-1 space-y-4 overflow-y-auto overflow-x-hidden px-3 py-4 [scrollbar-gutter:stable]">
      {groups.map((group, gi) => (
        <div
          key={group.label ?? `g${gi}`}
          // When collapsed the group label is hidden, so a hairline keeps the
          // groups visually separated instead of one long icon column.
          className={collapsed && gi > 0 ? "border-t border-slate-200/70 pt-4 dark:border-slate-800/70" : ""}
        >
          {group.label && !collapsed && (
            <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              {group.label}
            </p>
          )}
          <div className="space-y-1">
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={onNavigate}
                title={collapsed ? item.label : undefined}
                className={({ isActive }) =>
                  `group/nav relative flex items-center rounded-lg text-sm font-medium transition-colors ${
                    collapsed ? "justify-center p-2.5" : "gap-3 px-3 py-2"
                  } ${
                    isActive
                      ? "bg-brand-600 text-white shadow-sm"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                  }`
                }
              >
                <item.icon size={18} className="shrink-0" />
                {!collapsed && <span className="truncate">{item.label}</span>}
                {collapsed && (
                  // Hover label for the icon-only rail.
                  <span className="pointer-events-none absolute left-full z-50 ml-2 hidden whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-xs font-medium text-white shadow-lg group-hover/nav:block dark:bg-slate-700">
                    {item.label}
                  </span>
                )}
              </NavLink>
            ))}
          </div>
        </div>
      ))}
    </nav>
  );
}

function SidebarFooter({ collapsed }: { collapsed: boolean }) {
  const { user, logout } = useAuth();
  const displayName = user ? `${user.first_name || user.username} ${user.last_name || ""}`.trim() : "";

  if (collapsed) {
    return (
      <div className="flex flex-col items-center gap-2 border-t border-slate-200 p-3 dark:border-slate-800">
        <Avatar name={displayName || "?"} src={user?.avatar_url} size={34} />
        <button
          onClick={logout}
          aria-label="Chiqish"
          title="Chiqish"
          className="flex h-9 w-9 items-center justify-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        >
          <LogOut size={17} />
        </button>
      </div>
    );
  }

  return (
    <div className="border-t border-slate-200 p-4 dark:border-slate-800">
      <div className="flex items-center gap-3">
        <Avatar name={displayName || "?"} src={user?.avatar_url} size={36} />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-800 dark:text-slate-100">{displayName}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">{user && ROLE_LABEL[user.role]}</p>
        </div>
      </div>
      <button
        onClick={logout}
        className="mt-3 flex w-full items-center justify-center gap-2 rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
      >
        <LogOut size={15} />
        Chiqish
      </button>
    </div>
  );
}

function StatPill({
  icon: Icon,
  tone,
  children,
}: {
  icon: LucideIcon;
  tone: "brand" | "orange" | "amber";
  children: React.ReactNode;
}) {
  const tones: Record<typeof tone, string> = {
    brand: "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300",
    orange: "bg-orange-50 text-orange-700 dark:bg-orange-500/10 dark:text-orange-300",
    amber: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-300",
  };
  return (
    <span className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold ${tones[tone]}`}>
      <Icon size={14} className="shrink-0" />
      {children}
    </span>
  );
}

function TopBar({ onMenuClick }: { onMenuClick: () => void }) {
  const { user } = useAuth();
  const stats = useStudentTopStats();
  const notificationsPath = user ? `/${user.role.toLowerCase()}/notifications` : "/login";

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur md:px-6 dark:border-slate-800 dark:bg-slate-950/80">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          aria-label="Menyuni ochish"
          className="rounded-md p-2 text-slate-600 hover:bg-slate-100 md:hidden dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <Menu size={20} />
        </button>
        <div className="flex items-center gap-2 md:hidden">
          <img src={logoMark} alt="" className="h-8 w-8 shrink-0" />
          <p className="select-none text-base font-bold text-slate-900 dark:text-slate-50">
            School<span className="text-brand-500 dark:text-brand-400">OS</span>
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        {stats && (
          <div className="hidden select-none items-center gap-2 sm:flex">
            <StatPill icon={Gauge} tone="brand">
              {stats.level}-daraja
            </StatPill>
            <StatPill icon={Flame} tone="orange">
              {stats.currentStreak}
            </StatPill>
            <StatPill icon={Trophy} tone="amber">
              {stats.totalXp} XP
            </StatPill>
          </div>
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
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(SIDEBAR_KEY) === "1";
    } catch {
      return false;
    }
  });
  const location = useLocation();

  // Close the drawer whenever the route changes (covers back/forward nav too,
  // not just clicking a link — NavLink's own onClick wouldn't catch that).
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const toggleCollapsed = () => {
    setCollapsed((c) => {
      const next = !c;
      try {
        localStorage.setItem(SIDEBAR_KEY, next ? "1" : "0");
      } catch {
        /* storage blocked (private window) — the toggle still works for this session */
      }
      return next;
    });
  };

  return (
    <div
      className={`min-h-screen md:flex md:h-screen md:overflow-hidden ${
        vibrant
          ? "bg-gradient-to-br from-brand-50 via-slate-50 to-brand-50 dark:from-slate-950 dark:via-slate-950 dark:to-brand-950/30"
          : "bg-slate-50 dark:bg-slate-950"
      }`}
    >
      {/* Mobile drawer — always full width, never collapsed. */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            aria-label="Yopish"
            onClick={() => setMobileOpen(false)}
            className="absolute inset-0 bg-slate-900/40 dark:bg-black/60"
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col bg-white shadow-xl dark:bg-slate-900">
            <div className="flex items-center justify-end px-3 pt-3">
              <button
                onClick={() => setMobileOpen(false)}
                aria-label="Yopish"
                className="rounded-md p-2 text-slate-400 hover:bg-slate-100 dark:text-slate-500 dark:hover:bg-slate-800"
              >
                <X size={18} />
              </button>
            </div>
            <BrandHeader brand={brand} collapsed={false} />
            <SidebarNav groups={navGroups} collapsed={false} onNavigate={() => setMobileOpen(false)} />
            <SidebarFooter collapsed={false} />
          </aside>
        </div>
      )}

      {/* Desktop sidebar — collapsible to an icon rail. */}
      <aside
        className={`relative hidden shrink-0 flex-col border-r border-slate-200 bg-white transition-[width] duration-200 ease-out md:flex md:h-screen dark:border-slate-800 dark:bg-slate-900 ${
          collapsed ? "w-[76px]" : "w-64"
        }`}
      >
        <BrandHeader brand={brand} collapsed={collapsed} />
        <SidebarNav groups={navGroups} collapsed={collapsed} />
        <SidebarFooter collapsed={collapsed} />
        <button
          onClick={toggleCollapsed}
          aria-label={collapsed ? "Panelni yoyish" : "Panelni yig'ish"}
          title={collapsed ? "Yoyish" : "Yig'ish"}
          className="absolute -right-3 top-[72px] z-10 flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm transition-colors hover:text-brand-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:text-brand-400"
        >
          {collapsed ? <ChevronsRight size={14} /> : <ChevronsLeft size={14} />}
        </button>
      </aside>

      <div className="flex flex-1 flex-col md:h-screen md:min-h-0">
        <TopBar onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto p-4 md:p-6 [scrollbar-gutter:stable]">
          <Outlet />
        </main>
      </div>

      <PushPrompt />
    </div>
  );
}
