import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, X } from "lucide-react";
import { useState } from "react";

import { api } from "../lib/api";
import type { ParentContact, ParentLinkCode, ParentTelegramAccountItem } from "../types";
import { Field, Input, PrimaryButton, SecondaryButton } from "./form";
import { ErrorState, LoadingState } from "./states";

/** Lets a student register a parent's phone number for reference, then
 * generate a one-time code the parent types into the bot to link their own
 * Telegram chat — the bot can't message a phone number directly, the parent
 * has to start the chat themselves. */
export function ParentTelegramConnect() {
  const queryClient = useQueryClient();
  const [linkCode, setLinkCode] = useState<ParentLinkCode | null>(null);
  const [phone, setPhone] = useState<string | null>(null);

  const { data: contact, isLoading: contactLoading } = useQuery({
    queryKey: ["parent-contact"],
    queryFn: async () => (await api.get<ParentContact>("/auth/parent-contact/")).data,
  });

  const { data: accounts, isLoading: accountsLoading, isError } = useQuery({
    queryKey: ["telegram", "parent-accounts"],
    queryFn: async () =>
      (await api.get<ParentTelegramAccountItem[]>("/telegram/parent-accounts/")).data,
  });

  const savePhone = useMutation({
    mutationFn: async (value: string) =>
      (await api.patch<ParentContact>("/auth/parent-contact/", { parent_phone_number: value })).data,
    onSuccess: (data) => queryClient.setQueryData(["parent-contact"], data),
  });

  const generateCode = useMutation({
    mutationFn: async () => (await api.post<ParentLinkCode>("/telegram/parent-link-code/")).data,
    onSuccess: (data) => setLinkCode(data),
  });

  const unlink = useMutation({
    mutationFn: async (id: number) => api.delete(`/telegram/parent-accounts/${id}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["telegram", "parent-accounts"] }),
  });

  if (contactLoading || accountsLoading) return <LoadingState label="Yuklanmoqda..." />;
  if (isError || !accounts || !contact) return <ErrorState />;

  const phoneValue = phone ?? contact.parent_phone_number;

  return (
    <div className="space-y-4">
      <Field label="Ota-onaning telefon raqami">
        <div className="flex gap-2">
          <Input
            value={phoneValue}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+998 90 123 45 67"
          />
          <SecondaryButton
            type="button"
            onClick={() => phoneValue && savePhone.mutate(phoneValue)}
            disabled={savePhone.isPending || !phoneValue || phoneValue === contact.parent_phone_number}
          >
            {savePhone.isPending ? "Saqlanmoqda..." : "Saqlash"}
          </SecondaryButton>
        </div>
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
          Bu faqat ma'lumot uchun — xabar yuborish uchun ota-onangiz pastdagi kod orqali botga
          ulanishi kerak.
        </p>
      </Field>

      {accounts.length > 0 && (
        <div className="space-y-2">
          {accounts.map((account) => (
            <div
              key={account.id}
              className="flex items-center justify-between rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 dark:border-emerald-500/30 dark:bg-emerald-500/10"
            >
              <p className="flex items-center gap-1.5 text-sm font-medium text-emerald-800 dark:text-emerald-300">
                <CheckCircle2 className="h-4 w-4" />
                {account.telegram_username ? `@${account.telegram_username}` : "Bog'langan"}
              </p>
              <button
                onClick={() => unlink.mutate(account.id)}
                disabled={unlink.isPending}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {linkCode ? (
        <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 px-4 py-4 dark:border-slate-800 dark:bg-slate-800/50">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Ota-onangiz Telegramda <strong>@{linkCode.bot_username}</strong> botini ochib, shu
            kodni yuborsin: <code>/start {linkCode.code}</code>
          </p>
          <p className="text-center text-2xl font-bold tracking-widest text-slate-900 dark:text-slate-100">
            {linkCode.code}
          </p>
          <a
            href={`https://t.me/${linkCode.bot_username}?start=${linkCode.code}`}
            target="_blank"
            rel="noreferrer"
            className="block"
          >
            <PrimaryButton type="button" className="w-full">
              Botga havola
            </PrimaryButton>
          </a>
          <p className="text-center text-xs text-slate-400 dark:text-slate-500">Kod 10 daqiqa amal qiladi.</p>
        </div>
      ) : (
        <SecondaryButton onClick={() => generateCode.mutate()} disabled={generateCode.isPending}>
          {generateCode.isPending ? "Yuklanmoqda..." : "Ota-ona uchun kod olish"}
        </SecondaryButton>
      )}
    </div>
  );
}
