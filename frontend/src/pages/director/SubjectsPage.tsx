import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { ConfirmDialog } from "../../components/ConfirmDialog";
import { Input, PrimaryButton } from "../../components/form";
import { PageHeader } from "../../components/PageHeader";
import { Pagination } from "../../components/Pagination";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import type { Paginated, Subject } from "../../types";

export function SubjectsPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [confirmTarget, setConfirmTarget] = useState<Subject | null>(null);

  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(id);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ["subjects", { search: debouncedSearch, page }],
    queryFn: async () =>
      (
        await api.get<Paginated<Subject>>("/subjects/", {
          params: { search: debouncedSearch || undefined, page },
        })
      ).data,
    placeholderData: keepPreviousData,
  });

  const createSubject = useMutation({
    mutationFn: async () => (await api.post("/subjects/", { name })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subjects"] });
      setName("");
      setError(null);
    },
    onError: () => setError("Saqlashda xatolik. Bu fan allaqachon mavjud bo'lishi mumkin."),
  });

  const deleteSubject = useMutation({
    mutationFn: async (id: number) => api.delete(`/subjects/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["subjects"] });
      setConfirmTarget(null);
    },
  });

  const total = data?.count ?? 0;
  const isFiltering = debouncedSearch !== "";

  return (
    <div className="space-y-6">
      <PageHeader title="Fanlar" subtitle={total > 0 ? `Jami ${total} ta fan` : undefined} />

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            createSubject.mutate();
          }}
          className="flex flex-1 gap-2"
        >
          <Input
            placeholder="Fan nomi, masalan: Matematika"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <PrimaryButton type="submit" loading={createSubject.isPending}>
            Qo'shish
          </PrimaryButton>
        </form>
        <Input
          type="search"
          placeholder="Qidirish..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Fan qidirish"
          className="sm:w-64"
        />
      </div>
      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {data && data.results.length === 0 && !isFiltering && <EmptyState title="Hali fan yo'q" />}
      {data && data.results.length === 0 && isFiltering && (
        <EmptyState title="Hech narsa topilmadi" description="Boshqa nom bilan qidiring." />
      )}

      {data && data.results.length > 0 && (
        <>
          <ul
            aria-busy={isFetching}
            className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3"
          >
            {data.results.map((subject) => (
              <li
                key={subject.id}
                className="card flex items-center justify-between gap-2 px-4 py-3"
              >
                <span className="min-w-0 truncate text-slate-800 dark:text-slate-100">
                  {subject.name}
                </span>
                <button
                  onClick={() => setConfirmTarget(subject)}
                  className="shrink-0 text-sm text-red-600 hover:underline dark:text-red-400"
                >
                  O'chirish
                </button>
              </li>
            ))}
          </ul>

          <Pagination
            page={page}
            total={total}
            hasPrev={Boolean(data.previous)}
            hasNext={Boolean(data.next)}
            onPrev={() => setPage((p) => Math.max(1, p - 1))}
            onNext={() => setPage((p) => p + 1)}
            busy={isFetching}
          />
        </>
      )}

      {confirmTarget && (
        <ConfirmDialog
          title="Fanni o'chirish"
          confirmLabel="O'chirish"
          danger
          loading={deleteSubject.isPending}
          onConfirm={() => deleteSubject.mutate(confirmTarget.id)}
          onClose={() => setConfirmTarget(null)}
        >
          <span className="font-medium text-ink">{confirmTarget.name}</span> fani o'chirilsinmi? Bu
          amalni qaytarib bo'lmaydi.
        </ConfirmDialog>
      )}
    </div>
  );
}
