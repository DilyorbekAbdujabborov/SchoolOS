import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Copy, ExternalLink, Globe, Lock } from "lucide-react";
import { useEffect, useState } from "react";

import { api, getApiError } from "../lib/api";
import type { PublicProfileSettings as Settings } from "../types";
import { Field, PrimaryButton } from "./form";

/**
 * Lets a user claim a public-profile handle and choose whether the
 * `/p/<handle>/` card is visible to anyone. Opt-in: a fresh account is private
 * until the user both sets a handle and flips visibility on.
 */
export function PublicProfileSettings() {
  const queryClient = useQueryClient();
  const { data } = useQuery({
    queryKey: ["public-profile-settings"],
    queryFn: async () => (await api.get<Settings>("/auth/public-profile/")).data,
  });

  const [handle, setHandle] = useState("");
  const [isPublic, setIsPublic] = useState(false);
  const [copied, setCopied] = useState(false);

  // Seed the form once the saved settings arrive (and after a save re-fetches).
  useEffect(() => {
    if (data) {
      setHandle(data.handle ?? "");
      setIsPublic(data.is_profile_public);
    }
  }, [data]);

  const mutation = useMutation({
    mutationFn: async (payload: Settings) =>
      (await api.patch<Settings>("/auth/public-profile/", payload)).data,
    onSuccess: (saved) => {
      queryClient.setQueryData(["public-profile-settings"], saved);
      queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });

  const error = mutation.error ? getApiError(mutation.error) : null;
  const handleError = error?.errors?.handle?.[0] ?? null;
  const generalError =
    error && !handleError ? (error.errors?.is_profile_public?.[0] ?? error.detail) : null;

  const savedHandle = data?.handle ?? null;
  const savedPublic = data?.is_profile_public ?? false;
  const profileUrl = savedHandle ? `${window.location.origin}/p/${savedHandle}` : null;
  const isLive = savedPublic && Boolean(savedHandle);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate({ handle: handle.trim() || null, is_profile_public: isPublic });
  }

  async function copyLink() {
    if (!profileUrl) return;
    try {
      await navigator.clipboard.writeText(profileUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      /* clipboard blocked — the link is visible to copy by hand */
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <p className="text-sm text-ink-muted">
        Handle tanlang — profilingiz <span className="font-medium text-ink">/p/handle</span> havolasi
        orqali ochiladi. Email, telefon va shaxsiy ma'lumotlar hech qachon ko'rsatilmaydi.
      </p>

      <Field label="Handle" hint="2-30 ta belgi: kichik harf, raqam va defis.">
        <div className="flex items-center overflow-hidden rounded-lg border border-line-strong bg-surface focus-within:ring-2 focus-within:ring-brand-500/70">
          <span className="select-none border-r border-line-soft bg-surface-raised px-3 py-2 text-sm text-ink-subtle">
            /p/
          </span>
          <input
            value={handle}
            onChange={(e) => setHandle(e.target.value.toLowerCase().replace(/\s+/g, ""))}
            placeholder="dilyorbekdev"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-ink outline-none placeholder:text-ink-subtle"
          />
        </div>
        {handleError && <span className="mt-1 block text-xs text-rose-600 dark:text-rose-400">{handleError}</span>}
      </Field>

      <button
        type="button"
        onClick={() => setIsPublic((v) => !v)}
        className="flex w-full items-center justify-between gap-3 rounded-xl border border-line bg-surface-raised px-4 py-3 text-left"
      >
        <span className="flex items-center gap-3">
          <span
            className={`flex h-9 w-9 items-center justify-center rounded-lg ${
              isPublic
                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300"
                : "bg-surface text-ink-subtle"
            }`}
          >
            {isPublic ? <Globe size={18} /> : <Lock size={18} />}
          </span>
          <span className="min-w-0">
            <span className="block text-sm font-medium text-ink">
              {isPublic ? "Ommaviy profil" : "Yashirin profil"}
            </span>
            <span className="block text-xs text-ink-subtle">
              {isPublic ? "Havolaga kirgan har kim ko'radi" : "Faqat siz ko'rasiz"}
            </span>
          </span>
        </span>
        <span
          aria-hidden
          className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
            isPublic ? "bg-emerald-500" : "bg-ink-subtle/40"
          }`}
        >
          <span
            className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${
              isPublic ? "left-[22px]" : "left-0.5"
            }`}
          />
        </span>
      </button>

      {generalError && <p className="text-sm text-rose-600 dark:text-rose-400">{generalError}</p>}

      <div className="flex flex-wrap items-center gap-2">
        <PrimaryButton type="submit" loading={mutation.isPending}>
          Saqlash
        </PrimaryButton>
        {mutation.isSuccess && !mutation.isPending && (
          <span className="flex items-center gap-1 text-sm text-emerald-600 dark:text-emerald-400">
            <Check size={15} /> Saqlandi
          </span>
        )}
      </div>

      {profileUrl && (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-line-soft bg-surface-raised px-3 py-2.5 text-sm">
          <span className="min-w-0 flex-1 truncate text-ink-muted">{profileUrl}</span>
          <button type="button" onClick={copyLink} className="btn btn-secondary btn-sm">
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? "Nusxalandi" : "Nusxa"}
          </button>
          {isLive && (
            <a
              href={profileUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary btn-sm"
            >
              <ExternalLink size={14} /> Ochish
            </a>
          )}
        </div>
      )}

      {!isLive && savedHandle && (
        <p className="text-xs text-ink-subtle">
          Profil hozir yashirin — ko'rinishi uchun yuqoridagi tugmani yoqing va saqlang.
        </p>
      )}
    </form>
  );
}
