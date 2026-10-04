import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Lock, LockOpen } from "lucide-react";

import { api } from "../lib/api";
import { PrimaryButton, SecondaryButton } from "./form";

/**
 * Lets a teacher lift the School Time Lock for their classes during a lesson, so
 * students can use the platform while class is in session. Opening covers all of
 * the teacher's classes and auto-expires at the end of the current period, so a
 * forgotten window never leaves a class open past the bell. Shown on the teacher
 * dashboard; it only matters while the lock is active, but reads fine any time.
 */

interface ClassAccessClass {
  id: number;
  name: string;
  expires_at: string | null;
}

interface ClassAccessStatus {
  open: boolean;
  expires_at: string | null;
  classes: ClassAccessClass[];
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" });
}

export function ClassAccessControl() {
  const queryClient = useQueryClient();

  const { data: status } = useQuery({
    queryKey: ["class-access"],
    queryFn: async () => (await api.get<ClassAccessStatus>("/class-access/")).data,
    // The window expires on its own server-side; refetch now and then so the
    // card reflects that without the teacher reloading.
    refetchInterval: 60_000,
  });

  const open = useMutation({
    mutationFn: async () => (await api.post<ClassAccessStatus>("/class-access/")).data,
    onSuccess: (data) => queryClient.setQueryData(["class-access"], data),
  });

  const close = useMutation({
    mutationFn: async () => (await api.delete<ClassAccessStatus>("/class-access/")).data,
    onSuccess: (data) => queryClient.setQueryData(["class-access"], data),
  });

  // Nothing to offer a teacher with no classes.
  if (status && status.classes.length === 0) return null;

  const isOpen = Boolean(status?.open);
  const busy = open.isPending || close.isPending;

  return (
    <div
      className={`card flex flex-col gap-3 p-4 sm:flex-row sm:items-center ${
        isOpen ? "border-emerald-300 dark:border-emerald-500/40" : ""
      }`}
    >
      <span
        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
          isOpen
            ? "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300"
            : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300"
        }`}
      >
        {isOpen ? <LockOpen size={20} /> : <Lock size={20} />}
      </span>

      <div className="min-w-0 flex-1">
        <p className="font-medium text-ink">Dars vaqtida platforma</p>
        <p className="text-sm text-ink-muted">
          {isOpen && status?.expires_at
            ? `O'quvchilaringiz uchun ochiq — soat ${formatTime(status.expires_at)} gacha.`
            : "O'quvchilaringiz dars vaqtida platformadan foydalana olishi uchun oching."}
        </p>
      </div>

      <div className="shrink-0">
        {isOpen ? (
          <SecondaryButton onClick={() => close.mutate()} loading={busy}>
            Yopish
          </SecondaryButton>
        ) : (
          <PrimaryButton onClick={() => open.mutate()} loading={busy}>
            Darsda ochish
          </PrimaryButton>
        )}
      </div>
    </div>
  );
}
