import type { ReactNode } from "react";

import { AvatarUploader } from "./AvatarUploader";
import { Badge } from "./Badge";

/** The identity block every role's Profile page opens with — avatar, name,
 * role badge, email, and an optional row of role-specific stat chips. */
export function ProfileHeaderCard({
  name,
  email,
  roleLabel,
  stats,
}: {
  name: string;
  email: string | undefined;
  roleLabel: string;
  stats?: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-start">
        <AvatarUploader />
        <div className="min-w-0 flex-1 text-center sm:pt-2 sm:text-left">
          <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
            <h2 className="truncate text-lg font-bold text-slate-900 dark:text-slate-50">{name}</h2>
            <Badge tone="brand">{roleLabel}</Badge>
          </div>
          <p className="mt-0.5 truncate text-sm text-slate-500 dark:text-slate-400">{email}</p>
        </div>
      </div>
      {stats && <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3">{stats}</div>}
    </div>
  );
}
