import { useQuery } from "@tanstack/react-query";
import {
  Award,
  CalendarDays,
  Flame,
  GraduationCap,
  Shield,
  Sparkles,
  Trophy,
  UserX,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Avatar } from "../components/Avatar";
import { Logo } from "../components/Logo";
import { ThemeToggle } from "../components/ThemeToggle";
import { LoadingState } from "../components/states";
import { api } from "../lib/api";
import { getLevelInfo } from "../lib/gamification";
import { TONE_CHIP, TONE_TEXT, TONE_WELL, type Tone } from "../lib/tones";
import type { PublicProfile, Role } from "../types";

const ROLE_LABEL: Record<Role, string> = {
  director: "Direktor",
  teacher: "O'qituvchi",
  student: "O'quvchi",
};

const ROLE_TONE: Record<Role, Tone> = {
  director: "amber",
  teacher: "ember",
  student: "brand",
};

/** The page chrome shared by every state: a slim top bar over the canvas. */
function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-canvas">
      <header className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-5">
        <Link to="/" className="rounded-xl">
          <Logo subtitle="Maktab platformasi" />
        </Link>
        <ThemeToggle />
      </header>
      <main className="mx-auto max-w-3xl px-4 pb-16">{children}</main>
    </div>
  );
}

export function PublicProfilePage() {
  const { handle = "" } = useParams();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["public-profile", handle],
    retry: false,
    queryFn: async () => (await api.get<PublicProfile>(`/p/${handle}/`)).data,
  });

  if (isLoading) {
    return (
      <Shell>
        <LoadingState />
      </Shell>
    );
  }

  if (isError || !data) {
    return (
      <Shell>
        <div className="card flex flex-col items-center gap-3 px-6 py-16 text-center">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-surface-raised text-ink-subtle">
            <UserX size={26} />
          </span>
          <h1 className="text-xl font-bold text-ink">Profil topilmadi</h1>
          <p className="max-w-sm text-sm text-ink-muted">
            <span className="font-medium text-ink">/{handle}</span> bo'yicha ochiq profil yo'q —
            havola noto'g'ri yoki egasi profilni yashirin qoldirgan.
          </p>
          <Link to="/" className="btn btn-primary btn-md mt-2">
            Bosh sahifaga
          </Link>
        </div>
      </Shell>
    );
  }

  return (
    <Shell>
      <ProfileCard profile={data} />
      <p className="mt-6 text-center text-xs text-ink-subtle">
        <Link to="/" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
          SchoolOS
        </Link>{" "}
        bilan yaratilgan
      </p>
    </Shell>
  );
}

function ProfileCard({ profile }: { profile: PublicProfile }) {
  const role = profile.role;
  const tone = ROLE_TONE[role];

  return (
    <div className="card relative overflow-hidden">
      <span aria-hidden className={`absolute inset-x-0 top-0 h-1.5 ${TONE_WELL[tone]}`} />
      <span
        aria-hidden
        className={`absolute -right-16 -top-16 h-48 w-48 rounded-full ${TONE_WELL[tone]} blur-2xl`}
      />

      <div className="relative flex flex-col items-center gap-4 px-6 pb-6 pt-10 text-center">
        <span className={`rounded-full p-1 ring-2 ${TONE_TEXT[tone]} ring-current`}>
          <Avatar name={profile.full_name} src={profile.avatar_url} size={104} />
        </span>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">{profile.full_name}</h1>
          <p className="mt-1 text-sm text-ink-subtle">@{profile.handle}</p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-2">
          <span className={`chip ${TONE_CHIP[tone]}`}>{ROLE_LABEL[role]}</span>
          {profile.school_class_name && (
            <span className="chip bg-surface-raised text-ink-muted">
              <GraduationCap size={14} />
              {profile.school_class_name}
            </span>
          )}
          {profile.member_since && (
            <span className="chip bg-surface-raised text-ink-muted">
              <CalendarDays size={14} />
              {profile.member_since}-yildan
            </span>
          )}
        </div>
      </div>

      {profile.is_student && <StudentBody profile={profile} />}
      {profile.is_teacher && profile.bio && (
        <div className="border-t border-line-soft px-6 py-5">
          <p className="whitespace-pre-line text-center text-sm text-ink-muted">{profile.bio}</p>
        </div>
      )}
    </div>
  );
}

function StudentBody({ profile }: { profile: PublicProfile }) {
  const { level } = getLevelInfo(profile.total_xp ?? 0);
  const league = profile.league;
  const streak = profile.streak;
  const achievements = profile.achievements ?? [];

  return (
    <>
      <div className="grid grid-cols-2 gap-px border-t border-line-soft bg-line-soft sm:grid-cols-4">
        <Stat icon={Trophy} tone="brand" label="Daraja" value={level} />
        <Stat icon={Sparkles} tone="ember" label="Jami XP" value={profile.total_xp ?? 0} />
        <Stat
          icon={Shield}
          tone="amber"
          label="Liga"
          value={league ? `${league.icon} ${league.name.replace(" liga", "")}` : "—"}
        />
        <Stat icon={Flame} tone="rose" label="Seriya" value={`${streak?.current ?? 0} kun`} />
      </div>

      <div className="px-6 py-5">
        <div className="mb-3 flex items-center gap-2">
          <Award size={16} className={TONE_TEXT.amber} />
          <h2 className="text-sm font-semibold text-ink">Yutuqlar</h2>
          <span className="text-xs text-ink-subtle">{achievements.length}</span>
        </div>
        {achievements.length === 0 ? (
          <p className="text-sm text-ink-subtle">Hali yutuq ochilmagan.</p>
        ) : (
          <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {achievements.map((item) => (
              <li
                key={item.name}
                className="flex items-center gap-2.5 rounded-xl border border-line-soft bg-surface-raised px-3 py-2.5"
              >
                <span className="text-xl leading-none">{item.icon || "🏅"}</span>
                <span className="min-w-0 truncate text-sm font-medium text-ink">{item.name}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}

function Stat({
  icon: Icon,
  tone,
  label,
  value,
}: {
  icon: typeof Trophy;
  tone: Tone;
  label: string;
  value: string | number;
}) {
  return (
    <div className="bg-surface px-4 py-4 text-center">
      <span
        className={`mx-auto mb-1.5 flex h-8 w-8 items-center justify-center rounded-lg ${TONE_CHIP[tone]}`}
      >
        <Icon size={16} />
      </span>
      <p className="truncate text-base font-bold text-ink">{value}</p>
      <p className="mt-0.5 text-[11px] font-medium uppercase tracking-wide text-ink-subtle">
        {label}
      </p>
    </div>
  );
}
