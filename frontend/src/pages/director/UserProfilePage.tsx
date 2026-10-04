import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Award,
  ExternalLink,
  Flame,
  Globe,
  Lock,
  Shield,
  Sparkles,
  Trophy,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Avatar } from "../../components/Avatar";
import { Badge } from "../../components/Badge";
import { PageHeader } from "../../components/PageHeader";
import { ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import { getLevelInfo } from "../../lib/gamification";
import { TONE_CHIP, type Tone } from "../../lib/tones";
import type { FullUserProfile } from "../../types";

function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("uz-UZ", { day: "2-digit", month: "long", year: "numeric" });
}

export function UserProfilePage() {
  const { id = "" } = useParams();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["user-full-profile", id],
    retry: false,
    queryFn: async () => (await api.get<FullUserProfile>(`/users/${id}/profile/`)).data,
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader
        title="Foydalanuvchi profili"
        action={
          <Link to="/app/director/students" className="btn btn-secondary btn-md">
            <ArrowLeft size={16} /> O'quvchilar
          </Link>
        }
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState message="Profil yuklanmadi — foydalanuvchi topilmadi yoki ruxsat yo'q." />}
      {data && <ProfileBody profile={data} />}
    </div>
  );
}

function ProfileBody({ profile }: { profile: FullUserProfile }) {
  const identity = profile.is_student
    ? [
        { label: "PINFL", value: profile.pinfl || null },
        { label: "Passport", value: profile.passport_number || null },
        { label: "Jinsi", value: profile.gender_label || null },
        { label: "Tug'ilgan sana", value: formatDate(profile.birth_date) },
        { label: "Telefon", value: profile.phone_number || null },
        { label: "Ota-ona telefoni", value: profile.parent_phone_number || null },
        { label: "Viloyat", value: profile.region || null },
        { label: "Manzil", value: profile.address || null },
      ]
    : [{ label: "Telefon", value: profile.phone_number || null }];

  const account = [
    { label: "Email", value: profile.email },
    { label: "Login", value: profile.username },
    { label: "Rol", value: profile.role_label },
    { label: "Holat", value: profile.is_active ? "Faol" : "Bloklangan" },
    { label: "A'zo bo'lgan", value: formatDate(profile.date_joined) },
  ];

  return (
    <>
      <div className="card relative overflow-hidden">
        <span aria-hidden className="absolute inset-x-0 top-0 h-1 bg-brand-500" />
        <div className="flex flex-col items-center gap-4 p-6 sm:flex-row sm:items-start">
          <span className="rounded-full ring-2 ring-brand-500/40">
            <Avatar name={profile.full_name} src={profile.avatar_url} size={88} />
          </span>
          <div className="min-w-0 flex-1 text-center sm:pt-1 sm:text-left">
            <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
              <h2 className="truncate text-xl font-bold tracking-tight text-ink">
                {profile.full_name}
              </h2>
              <Badge tone="brand">{profile.role_label}</Badge>
              {!profile.is_active && <Badge tone="rose">Bloklangan</Badge>}
            </div>
            <div className="mt-1 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-sm text-ink-muted sm:justify-start">
              {profile.handle && <span>@{profile.handle}</span>}
              {profile.school_class_name && <span>{profile.school_class_name}</span>}
              {profile.member_since && <span>{profile.member_since}-yildan</span>}
            </div>
          </div>
        </div>

        {profile.is_student && <StatStrip profile={profile} />}
      </div>

      {profile.is_student && (
        <div className="card p-6">
          <h3 className="mb-3 font-semibold text-ink">Shaxsiy ma'lumotlar</h3>
          <DataList rows={identity} />
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-3 font-semibold text-ink">Hisob ma'lumotlari</h3>
          <DataList rows={account} />
        </div>

        <div className="card p-6">
          <h3 className="mb-3 font-semibold text-ink">Ommaviy profil</h3>
          <div className="flex items-center gap-2 text-sm">
            {profile.is_profile_public && profile.handle ? (
              <>
                <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                  <Globe size={15} /> Ochiq
                </span>
                <a
                  href={`/p/${profile.handle}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-sm ml-auto"
                >
                  <ExternalLink size={14} /> /p/{profile.handle}
                </a>
              </>
            ) : (
              <span className="flex items-center gap-1.5 text-ink-muted">
                <Lock size={15} /> Yashirin
              </span>
            )}
          </div>
        </div>
      </div>

      {profile.is_teacher && profile.bio && (
        <div className="card p-6">
          <h3 className="mb-2 font-semibold text-ink">Bio</h3>
          <p className="whitespace-pre-line text-sm text-ink-muted">{profile.bio}</p>
        </div>
      )}

      {profile.is_student && (
        <div className="card p-6">
          <div className="mb-3 flex items-center gap-2">
            <Award size={16} className="text-amber-600 dark:text-amber-400" />
            <h3 className="font-semibold text-ink">Yutuqlar</h3>
            <span className="text-xs text-ink-subtle">{profile.achievements?.length ?? 0}</span>
          </div>
          {!profile.achievements || profile.achievements.length === 0 ? (
            <p className="text-sm text-ink-subtle">Hali yutuq ochilmagan.</p>
          ) : (
            <ul className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {profile.achievements.map((item) => (
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
      )}
    </>
  );
}

function StatStrip({ profile }: { profile: FullUserProfile }) {
  const { level } = getLevelInfo(profile.total_xp ?? 0);
  const league = profile.league;
  const streak = profile.streak;
  return (
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

function DataList({ rows }: { rows: { label: string; value: string | null }[] }) {
  return (
    <dl className="space-y-2 text-sm">
      {rows.map((row) => (
        <div key={row.label} className="flex justify-between gap-4">
          <dt className="text-ink-muted">{row.label}</dt>
          <dd className="truncate text-ink">{row.value ?? "—"}</dd>
        </div>
      ))}
    </dl>
  );
}
