import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useState } from "react";

import { Badge } from "../../components/Badge";
import { Field, Input, PrimaryButton, Select, SecondaryButton } from "../../components/form";
import { Modal } from "../../components/Modal";
import { PageHeader } from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { Table, Tbody, Td, Th, Thead, Tr } from "../../components/table";
import { api } from "../../lib/api";
import type { Paginated, SchoolClass, Student } from "../../types";

const PAGE_SIZE = 20;

interface StudentFormState {
  email: string;
  first_name: string;
  last_name: string;
  school_class: string;
  password: string;
}

const EMPTY_FORM: StudentFormState = {
  email: "",
  first_name: "",
  last_name: "",
  school_class: "",
  password: "",
};

export function StudentsPage() {
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<StudentFormState>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  // List controls. `search` is what the user types; `debouncedSearch` is what
  // actually hits the API, so every keystroke doesn't fire a request.
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [classFilter, setClassFilter] = useState("");
  const [page, setPage] = useState(1);
  const [confirmTarget, setConfirmTarget] = useState<Student | null>(null);

  useEffect(() => {
    const id = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(id);
  }, [search]);

  // Any filter change sends us back to the first page — otherwise you can land
  // on page 5 of a result set that now has one page.
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, classFilter]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: ["students", { search: debouncedSearch, schoolClass: classFilter, page }],
    queryFn: async () =>
      (
        await api.get<Paginated<Student>>("/students/", {
          params: {
            search: debouncedSearch || undefined,
            school_class: classFilter || undefined,
            page,
          },
        })
      ).data,
    placeholderData: keepPreviousData,
  });

  const { data: classes } = useQuery({
    queryKey: ["classes"],
    queryFn: async () => (await api.get<Paginated<SchoolClass>>("/classes/")).data,
  });

  const createStudent = useMutation({
    mutationFn: async (payload: StudentFormState) =>
      (
        await api.post("/students/", {
          ...payload,
          school_class: payload.school_class ? Number(payload.school_class) : null,
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
      queryClient.invalidateQueries({ queryKey: ["classes"] });
      setModalOpen(false);
      setForm(EMPTY_FORM);
      setError(null);
    },
    onError: () => setError("Saqlashda xatolik. Email band bo'lishi mumkin."),
  });

  const toggleActive = useMutation({
    mutationFn: async (student: Student) =>
      (await api.patch(`/students/${student.id}/`, { is_active: !student.is_active })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
      setConfirmTarget(null);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    createStudent.mutate(form);
  }

  const total = data?.count ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = Math.min(page * PAGE_SIZE, total);
  const isFiltering = debouncedSearch !== "" || classFilter !== "";

  return (
    <div className="space-y-6">
      <PageHeader
        title="O'quvchilar"
        subtitle={total > 0 ? `Jami ${total} ta o'quvchi` : undefined}
        action={<PrimaryButton onClick={() => setModalOpen(true)}>+ O'quvchi qo'shish</PrimaryButton>}
      />

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Input
            type="search"
            placeholder="Ism yoki email bo'yicha qidirish..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="O'quvchi qidirish"
          />
        </div>
        <Select
          value={classFilter}
          onChange={(e) => setClassFilter(e.target.value)}
          aria-label="Sinf bo'yicha filtr"
          className="sm:w-56"
        >
          <option value="">Barcha sinflar</option>
          {classes?.results.map((cls) => (
            <option key={cls.id} value={cls.id}>
              {cls.name}
            </option>
          ))}
        </Select>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {data && data.results.length === 0 && !isFiltering && (
        <EmptyState title="Hali o'quvchi yo'q" description="Yuqoridagi tugma orqali qo'shing." />
      )}
      {data && data.results.length === 0 && isFiltering && (
        <EmptyState
          title="Hech narsa topilmadi"
          description="Qidiruv yoki filtrni o'zgartirib ko'ring."
        />
      )}

      {data && data.results.length > 0 && (
        <>
          <div aria-busy={isFetching}>
            <Table>
              <Thead>
                <Tr>
                  <Th>Ism</Th>
                  <Th>Sinf</Th>
                  <Th>Holat</Th>
                  <Th />
                </Tr>
              </Thead>
              <Tbody>
                {data.results.map((student) => (
                  <Tr key={student.id}>
                    <Td className="font-medium capitalize text-slate-900 dark:text-slate-50">
                      {student.first_name.toLocaleLowerCase("uz")}{" "}
                      {student.last_name.toLocaleLowerCase("uz")}
                    </Td>
                    <Td className="text-slate-600 dark:text-slate-300">
                      {student.school_class_name ?? (
                        <span className="text-ink-subtle">—</span>
                      )}
                    </Td>
                    <Td>
                      <Badge tone={student.is_active ? "emerald" : "slate"}>
                        {student.is_active ? "Faol" : "Faol emas"}
                      </Badge>
                    </Td>
                    <Td className="text-right">
                      <button
                        onClick={() => setConfirmTarget(student)}
                        className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
                      >
                        {student.is_active ? "Faolsizlantirish" : "Faollashtirish"}
                      </button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-ink-muted">
              {rangeStart}–{rangeEnd} / {total}
            </p>
            <div className="flex items-center gap-2">
              <SecondaryButton
                type="button"
                disabled={!data.previous || isFetching}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Oldingi
              </SecondaryButton>
              <span className="text-sm text-ink-muted">
                {page} / {totalPages}
              </span>
              <SecondaryButton
                type="button"
                disabled={!data.next || isFetching}
                onClick={() => setPage((p) => p + 1)}
              >
                Keyingi
              </SecondaryButton>
            </div>
          </div>
        </>
      )}

      {confirmTarget && (
        <Modal
          title={confirmTarget.is_active ? "O'quvchini faolsizlantirish" : "O'quvchini faollashtirish"}
          onClose={() => setConfirmTarget(null)}
        >
          <p className="text-sm text-ink-muted">
            <span className="font-medium text-ink">
              {confirmTarget.first_name} {confirmTarget.last_name}
            </span>{" "}
            {confirmTarget.is_active
              ? "faolsizlantirilsinmi? U tizimga kira olmaydi."
              : "qayta faollashtirilsinmi?"}
          </p>
          <div className="flex justify-end gap-2 pt-4">
            <SecondaryButton type="button" onClick={() => setConfirmTarget(null)}>
              Bekor qilish
            </SecondaryButton>
            <PrimaryButton
              type="button"
              disabled={toggleActive.isPending}
              onClick={() => toggleActive.mutate(confirmTarget)}
            >
              {toggleActive.isPending ? "Bajarilmoqda..." : "Tasdiqlash"}
            </PrimaryButton>
          </div>
        </Modal>
      )}

      {isModalOpen && (
        <Modal title="O'quvchi qo'shish" onClose={() => setModalOpen(false)}>
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
            <Field label="Sinf">
              <Select
                value={form.school_class}
                onChange={(e) => setForm({ ...form, school_class: e.target.value })}
              >
                <option value="">— tanlanmagan —</option>
                {classes?.results.map((cls) => (
                  <option key={cls.id} value={cls.id}>
                    {cls.name}
                  </option>
                ))}
              </Select>
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
              <PrimaryButton type="submit" disabled={createStudent.isPending}>
                {createStudent.isPending ? "Saqlanmoqda..." : "Saqlash"}
              </PrimaryButton>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
