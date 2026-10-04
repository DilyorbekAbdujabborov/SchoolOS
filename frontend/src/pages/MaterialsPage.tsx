import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AxiosError } from "axios";
import {
  Archive,
  Download,
  ExternalLink,
  File as FileIcon,
  FileText,
  Image as ImageIcon,
  Link as LinkIcon,
  Music,
  Presentation,
  Sheet,
  Trash2,
  Video,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { type FormEvent, useEffect, useState } from "react";

import { Badge } from "../components/Badge";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Field, Input, PrimaryButton, SecondaryButton, Select, Textarea } from "../components/form";
import { Modal } from "../components/Modal";
import { PageHeader } from "../components/PageHeader";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorState, LoadingState } from "../components/states";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import type { Material, MaterialKind, Paginated, Subject } from "../types";

/** Icon + accent per material kind, so the library reads at a glance. */
const KIND_STYLE: Record<MaterialKind, { icon: LucideIcon; className: string }> = {
  LINK: { icon: LinkIcon, className: "bg-brand-100 text-brand-600 dark:bg-brand-500/15 dark:text-brand-300" },
  PDF: { icon: FileText, className: "bg-rose-100 text-rose-600 dark:bg-rose-500/15 dark:text-rose-300" },
  DOC: { icon: FileText, className: "bg-sky-100 text-sky-600 dark:bg-sky-500/15 dark:text-sky-300" },
  SHEET: { icon: Sheet, className: "bg-emerald-100 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300" },
  SLIDES: { icon: Presentation, className: "bg-amber-100 text-amber-600 dark:bg-amber-500/15 dark:text-amber-300" },
  IMAGE: { icon: ImageIcon, className: "bg-violet-100 text-violet-600 dark:bg-violet-500/15 dark:text-violet-300" },
  VIDEO: { icon: Video, className: "bg-fuchsia-100 text-fuchsia-600 dark:bg-fuchsia-500/15 dark:text-fuchsia-300" },
  AUDIO: { icon: Music, className: "bg-cyan-100 text-cyan-600 dark:bg-cyan-500/15 dark:text-cyan-300" },
  ARCHIVE: { icon: Archive, className: "bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-200" },
  OTHER: { icon: FileIcon, className: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300" },
};

const KIND_OPTIONS: { value: MaterialKind; label: string }[] = [
  { value: "LINK", label: "Havola" },
  { value: "PDF", label: "PDF" },
  { value: "DOC", label: "Hujjat" },
  { value: "SHEET", label: "Jadval" },
  { value: "SLIDES", label: "Taqdimot" },
  { value: "IMAGE", label: "Rasm" },
  { value: "VIDEO", label: "Video" },
  { value: "AUDIO", label: "Audio" },
  { value: "ARCHIVE", label: "Arxiv" },
  { value: "OTHER", label: "Boshqa" },
];

function formatSize(bytes: number | null): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface FormState {
  title: string;
  description: string;
  subject: string;
  link: string;
  file: File | null;
}

const EMPTY_FORM: FormState = { title: "", description: "", subject: "", link: "", file: null };

export function MaterialsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canManage = user?.role === "TEACHER" || user?.role === "DIRECTOR";

  const [subjectFilter, setSubjectFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);

  const [isModalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [confirmTarget, setConfirmTarget] = useState<Material | null>(null);

  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(id);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [subjectFilter, kindFilter, debouncedSearch]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ["materials", { subject: subjectFilter, kind: kindFilter, search: debouncedSearch, page }],
    queryFn: async () =>
      (
        await api.get<Paginated<Material>>("/materials/", {
          params: {
            subject: subjectFilter || undefined,
            kind: kindFilter || undefined,
            search: debouncedSearch || undefined,
            page,
          },
        })
      ).data,
    placeholderData: keepPreviousData,
  });

  const { data: subjects } = useQuery({
    queryKey: ["subjects"],
    queryFn: async () => (await api.get<Paginated<Subject>>("/subjects/")).data,
  });

  const createMaterial = useMutation({
    mutationFn: async (payload: FormState) => {
      const body = new FormData();
      body.append("title", payload.title);
      body.append("description", payload.description);
      body.append("subject", payload.subject);
      if (payload.file) body.append("file", payload.file);
      if (payload.link) body.append("link", payload.link);
      return (await api.post("/materials/", body)).data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials"] });
      setModalOpen(false);
      setForm(EMPTY_FORM);
      setError(null);
    },
    onError: (err) => {
      if (err instanceof AxiosError && err.response?.status === 413) {
        setError("Fayl juda katta (maks 20MB). Kattaroq fayl uchun havola (URL) kiriting.");
        return;
      }
      setError("Saqlashda xatolik. Fayl yoki havola, fan va sarlavhani tekshiring.");
    },
  });

  const deleteMaterial = useMutation({
    mutationFn: async (material: Material) => api.delete(`/materials/${material.id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["materials"] });
      setConfirmTarget(null);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.file && !form.link.trim()) {
      setError("Fayl yoki havola kiritilishi shart.");
      return;
    }
    createMaterial.mutate(form);
  }

  const total = data?.count ?? 0;
  const materials = data?.results ?? [];
  const isFiltering = Boolean(subjectFilter || kindFilter || debouncedSearch);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Materiallar"
        subtitle={total > 0 ? `Kutubxonada ${total} ta material` : "O'quv materiallari kutubxonasi"}
        action={
          canManage ? (
            <PrimaryButton onClick={() => setModalOpen(true)}>+ Material qo'shish</PrimaryButton>
          ) : undefined
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          type="search"
          placeholder="Material qidirish..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Material qidirish"
          className="flex-1"
        />
        <Select
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
          aria-label="Fan bo'yicha filtr"
          className="sm:w-48"
        >
          <option value="">Barcha fanlar</option>
          {subjects?.results.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </Select>
        <Select
          value={kindFilter}
          onChange={(e) => setKindFilter(e.target.value)}
          aria-label="Tur bo'yicha filtr"
          className="sm:w-44"
        >
          <option value="">Barcha turlar</option>
          {KIND_OPTIONS.map((k) => (
            <option key={k.value} value={k.value}>
              {k.label}
            </option>
          ))}
        </Select>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {data && materials.length === 0 && (
        <EmptyState
          title={isFiltering ? "Hech narsa topilmadi" : "Hali material yo'q"}
          description={
            isFiltering
              ? "Qidiruv yoki filtrni o'zgartirib ko'ring."
              : canManage
                ? "Yuqoridagi tugma orqali birinchi materialni qo'shing."
                : "Tez orada o'qituvchilaringiz material joylaydi."
          }
        />
      )}

      {materials.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-busy={isFetching}>
          {materials.map((material) => {
            const style = KIND_STYLE[material.kind] ?? KIND_STYLE.OTHER;
            const href = material.file_url ?? material.link;
            const canDelete = canManage;
            return (
              <div key={material.id} className="card flex flex-col gap-3 p-4">
                <div className="flex items-start gap-3">
                  <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${style.className}`}>
                    <style.icon size={20} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-ink">{material.title}</p>
                    <p className="text-xs text-ink-muted">
                      {material.subject_name}
                      {material.file_size ? ` · ${formatSize(material.file_size)}` : ""}
                    </p>
                  </div>
                  {canDelete && (
                    <button
                      onClick={() => setConfirmTarget(material)}
                      aria-label="O'chirish"
                      className="shrink-0 rounded-md p-1.5 text-ink-subtle transition-colors hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-500/10"
                    >
                      <Trash2 size={16} />
                    </button>
                  )}
                </div>

                {material.description && (
                  <p className="line-clamp-2 text-sm text-ink-muted">{material.description}</p>
                )}

                <div className="mt-auto flex items-center justify-between gap-2 pt-1">
                  <Badge tone="slate">{material.kind_display}</Badge>
                  {href && (
                    <a
                      href={href}
                      target="_blank"
                      rel="noreferrer noopener"
                      className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
                    >
                      {material.file_url ? <Download size={15} /> : <ExternalLink size={15} />}
                      {material.file_url ? "Yuklab olish" : "Ochish"}
                    </a>
                  )}
                </div>

                {material.uploaded_by_name && (
                  <p className="text-xs text-ink-subtle">
                    {material.uploaded_by_name} ·{" "}
                    {new Date(material.created_at).toLocaleDateString("uz-UZ")}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {total > 0 && (
        <Pagination
          page={page}
          total={total}
          hasPrev={Boolean(data?.previous)}
          hasNext={Boolean(data?.next)}
          onPrev={() => setPage((p) => Math.max(1, p - 1))}
          onNext={() => setPage((p) => p + 1)}
          busy={isFetching}
        />
      )}

      {confirmTarget && (
        <ConfirmDialog
          title="Materialni o'chirish"
          confirmLabel="O'chirish"
          danger
          loading={deleteMaterial.isPending}
          onConfirm={() => deleteMaterial.mutate(confirmTarget)}
          onClose={() => setConfirmTarget(null)}
        >
          <span className="font-medium text-ink">{confirmTarget.title}</span> o'chirilsinmi? Bu amalni
          qaytarib bo'lmaydi.
        </ConfirmDialog>
      )}

      {isModalOpen && (
        <Modal title="Material qo'shish" onClose={() => setModalOpen(false)}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Sarlavha">
              <Input
                required
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </Field>
            <Field label="Fan">
              <Select
                required
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
              >
                <option value="">— fan tanlang —</option>
                {subjects?.results.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Tavsif (ixtiyoriy)">
              <Textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </Field>
            <Field label="Fayl" hint="Har qanday fayl: PDF, Word, rasm, video, taqdimot...">
              <input
                type="file"
                onChange={(e) => setForm({ ...form, file: e.target.files?.[0] ?? null })}
                className="block w-full text-sm text-ink-muted file:mr-3 file:rounded-lg file:border-0 file:bg-brand-50 file:px-4 file:py-2 file:text-sm file:font-medium file:text-brand-700 hover:file:bg-brand-100 dark:file:bg-brand-500/15 dark:file:text-brand-300"
              />
            </Field>
            <Field label="Yoki havola" hint="YouTube, Google Drive yoki boshqa URL">
              <Input
                type="url"
                placeholder="https://..."
                value={form.link}
                onChange={(e) => setForm({ ...form, link: e.target.value })}
              />
            </Field>
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <SecondaryButton type="button" onClick={() => setModalOpen(false)}>
                Bekor qilish
              </SecondaryButton>
              <PrimaryButton type="submit" disabled={createMaterial.isPending}>
                {createMaterial.isPending ? "Saqlanmoqda..." : "Saqlash"}
              </PrimaryButton>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
