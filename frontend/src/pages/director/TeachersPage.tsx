import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useState } from "react";

import { Badge } from "../../components/Badge";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { Field, Input, PrimaryButton, SecondaryButton } from "../../components/form";
import { Modal } from "../../components/Modal";
import { PageHeader } from "../../components/PageHeader";
import { Pagination } from "../../components/Pagination";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { Table, Tbody, Td, Th, Thead, Tr } from "../../components/table";
import { api } from "../../lib/api";
import type { Paginated, Teacher } from "../../types";

interface TeacherFormState {
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  password: string;
}

const EMPTY_FORM: TeacherFormState = {
  email: "",
  first_name: "",
  last_name: "",
  phone_number: "",
  password: "",
};

export function TeachersPage() {
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<TeacherFormState>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [page, setPage] = useState(1);
  const [confirmTarget, setConfirmTarget] = useState<Teacher | null>(null);

  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(id);
  }, [search]);

  useEffect(() => {
    setPage(1);
  }, [debouncedSearch]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ["teachers", { search: debouncedSearch, page }],
    queryFn: async () =>
      (
        await api.get<Paginated<Teacher>>("/teachers/", {
          params: { search: debouncedSearch || undefined, page },
        })
      ).data,
    placeholderData: keepPreviousData,
  });

  const createTeacher = useMutation({
    mutationFn: async (payload: TeacherFormState) => (await api.post("/teachers/", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers"] });
      setModalOpen(false);
      setForm(EMPTY_FORM);
      setError(null);
    },
    onError: () => setError("Saqlashda xatolik. Email band bo'lishi mumkin."),
  });

  const toggleActive = useMutation({
    mutationFn: async (teacher: Teacher) =>
      (await api.patch(`/teachers/${teacher.id}/`, { is_active: !teacher.is_active })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers"] });
      setConfirmTarget(null);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    createTeacher.mutate(form);
  }

  const total = data?.count ?? 0;
  const isFiltering = debouncedSearch !== "";

  return (
    <div className="space-y-6">
      <PageHeader
        title="O'qituvchilar"
        subtitle={total > 0 ? `Jami ${total} ta o'qituvchi` : undefined}
        action={<PrimaryButton onClick={() => setModalOpen(true)}>+ O'qituvchi qo'shish</PrimaryButton>}
      />

      <Input
        type="search"
        placeholder="Ism yoki email bo'yicha qidirish..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        aria-label="O'qituvchi qidirish"
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {data && data.results.length === 0 && !isFiltering && (
        <EmptyState title="Hali o'qituvchi yo'q" description="Yuqoridagi tugma orqali qo'shing." />
      )}
      {data && data.results.length === 0 && isFiltering && (
        <EmptyState title="Hech narsa topilmadi" description="Qidiruvni o'zgartirib ko'ring." />
      )}

      {data && data.results.length > 0 && (
        <>
          <div aria-busy={isFetching}>
            <Table>
              <Thead>
                <Tr>
                  <Th>Ism</Th>
                  <Th>Telefon</Th>
                  <Th>Holat</Th>
                  <Th />
                </Tr>
              </Thead>
              <Tbody>
                {data.results.map((teacher) => (
                  <Tr key={teacher.id}>
                    <Td className="font-medium text-slate-900 dark:text-slate-50">
                      {teacher.first_name} {teacher.last_name}
                    </Td>
                    <Td className="text-slate-600 dark:text-slate-300">
                      {teacher.phone_number || <span className="text-ink-subtle">—</span>}
                    </Td>
                    <Td>
                      <Badge tone={teacher.is_active ? "emerald" : "slate"}>
                        {teacher.is_active ? "Faol" : "Faol emas"}
                      </Badge>
                    </Td>
                    <Td className="text-right">
                      <button
                        onClick={() => setConfirmTarget(teacher)}
                        className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
                      >
                        {teacher.is_active ? "Faolsizlantirish" : "Faollashtirish"}
                      </button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>

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
          title={
            confirmTarget.is_active ? "O'qituvchini faolsizlantirish" : "O'qituvchini faollashtirish"
          }
          confirmLabel={confirmTarget.is_active ? "Faolsizlantirish" : "Faollashtirish"}
          danger={confirmTarget.is_active}
          loading={toggleActive.isPending}
          onConfirm={() => toggleActive.mutate(confirmTarget)}
          onClose={() => setConfirmTarget(null)}
        >
          <span className="font-medium text-ink">
            {confirmTarget.first_name} {confirmTarget.last_name}
          </span>{" "}
          {confirmTarget.is_active
            ? "faolsizlantirilsinmi? U tizimga kira olmaydi."
            : "qayta faollashtirilsinmi?"}
        </ConfirmDialog>
      )}

      {isModalOpen && (
        <Modal title="O'qituvchi qo'shish" onClose={() => setModalOpen(false)}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Field label="Email">
              <Input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Ism">
                <Input
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                />
              </Field>
              <Field label="Familiya">
                <Input
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                />
              </Field>
            </div>
            <Field label="Telefon">
              <Input
                value={form.phone_number}
                onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
              />
            </Field>
            <Field label="Vaqtinchalik parol">
              <Input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </Field>
            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <SecondaryButton type="button" onClick={() => setModalOpen(false)}>
                Bekor qilish
              </SecondaryButton>
              <PrimaryButton type="submit" disabled={createTeacher.isPending}>
                {createTeacher.isPending ? "Saqlanmoqda..." : "Saqlash"}
              </PrimaryButton>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
