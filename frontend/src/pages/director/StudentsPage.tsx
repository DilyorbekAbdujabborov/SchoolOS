import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useState } from "react";

import { Avatar } from "../../components/Avatar";
import { Badge } from "../../components/Badge";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { Field, Input, PrimaryButton, Select, SecondaryButton } from "../../components/form";
import { Modal } from "../../components/Modal";
import { PageHeader } from "../../components/PageHeader";
import { Pagination } from "../../components/Pagination";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { Table, Tbody, Td, Th, Thead, Tr } from "../../components/table";
import { api } from "../../lib/api";
import type { Paginated, SchoolClass, Student } from "../../types";

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

/** Title-case a name the way the DB stores it, lowercasing with Uzbek rules. */
function displayName(student: Student): string {
  return `${student.first_name} ${student.last_name}`.trim();
}

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
  const [statusFilter, setStatusFilter] = useState("");
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
  }, [debouncedSearch, classFilter, statusFilter]);

  const { data, isLoading, isError, isFetching } = useQuery({
    queryKey: [
      "students",
      { search: debouncedSearch, schoolClass: classFilter, status: statusFilter, page },
    ],
    queryFn: async () =>
      (
        await api.get<Paginated<Student>>("/app/students/", {
          params: {
            search: debouncedSearch || undefined,
            school_class: classFilter || undefined,
            is_active: statusFilter || undefined,
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
        await api.post("/app/students/", {
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
      (await api.patch(`/app/students/${student.id}/`, { is_active: !student.is_active })).data,
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
  const isFiltering = debouncedSearch !== "" || classFilter !== "" || statusFilter !== "";
  const students = data?.results ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="O'quvchilar"
        subtitle={total > 0 ? `Jami ${total} ta o'quvchi` : undefined}
        action={<PrimaryButton onClick={() => setModalOpen(true)}>+ O'quvchi qo'shish</PrimaryButton>}
      />

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          type="search"
          placeholder="Ism yoki email bo'yicha qidirish..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="O'quvchi qidirish"
          className="flex-1"
        />
        <Select
          value={classFilter}
          onChange={(e) => setClassFilter(e.target.value)}
          aria-label="Sinf bo'yicha filtr"
          className="sm:w-48"
        >
          <option value="">Barcha sinflar</option>
          {classes?.results.map((cls) => (
            <option key={cls.id} value={cls.id}>
              {cls.name}
            </option>
          ))}
        </Select>
        <Select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          aria-label="Holat bo'yicha filtr"
          className="sm:w-40"
        >
          <option value="">Barcha holatlar</option>
          <option value="true">Faol</option>
          <option value="false">Faol emas</option>
        </Select>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {data && students.length === 0 && !isFiltering && (
        <EmptyState title="Hali o'quvchi yo'q" description="Yuqoridagi tugma orqali qo'shing." />
      )}
      {data && students.length === 0 && isFiltering && (
        <EmptyState
          title="Hech narsa topilmadi"
          description="Qidiruv yoki filtrni o'zgartirib ko'ring."
        />
      )}

      {students.length > 0 && (
        <div className="space-y-4" aria-busy={isFetching}>
          {/* Desktop: table. Mobile: stacked cards (below). */}
          <div className="hidden sm:block">
            <Table>
              <Thead>
                <Tr>
                  <Th>O'quvchi</Th>
                  <Th>Sinf</Th>
                  <Th className="text-right">XP</Th>
                  <Th>Holat</Th>
                  <Th />
                </Tr>
              </Thead>
              <Tbody>
                {students.map((student) => (
                  <Tr key={student.id}>
                    <Td>
                      <div className="flex items-center gap-3">
                        <Avatar name={displayName(student)} size={36} />
                        <div className="min-w-0">
                          <p className="truncate font-medium capitalize text-slate-900 dark:text-slate-50">
                            {displayName(student).toLocaleLowerCase("uz")}
                          </p>
                          <p className="truncate text-xs text-ink-muted">{student.email}</p>
                        </div>
                      </div>
                    </Td>
                    <Td className="text-slate-600 dark:text-slate-300">
                      {student.school_class_name ?? <span className="text-ink-subtle">—</span>}
                    </Td>
                    <Td className="text-right font-medium tabular-nums text-amber-600 dark:text-amber-400">
                      {student.total_xp.toLocaleString("uz-UZ")}
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

          {/* Mobile cards */}
          <ul className="space-y-3 sm:hidden">
            {students.map((student) => (
              <li key={student.id} className="card space-y-3 p-4">
                <div className="flex items-start gap-3">
                  <Avatar name={displayName(student)} size={40} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium capitalize text-slate-900 dark:text-slate-50">
                      {displayName(student).toLocaleLowerCase("uz")}
                    </p>
                    <p className="truncate text-xs text-ink-muted">{student.email}</p>
                  </div>
                  <Badge tone={student.is_active ? "emerald" : "slate"}>
                    {student.is_active ? "Faol" : "Faol emas"}
                  </Badge>
                </div>
                <div className="flex items-center justify-between gap-2 text-sm">
                  <span className="text-ink-muted">
                    {student.school_class_name ?? "Sinfsiz"} ·{" "}
                    <span className="font-medium text-amber-600 dark:text-amber-400">
                      {student.total_xp.toLocaleString("uz-UZ")} XP
                    </span>
                  </span>
                  <button
                    onClick={() => setConfirmTarget(student)}
                    className="shrink-0 font-medium text-brand-600 hover:underline dark:text-brand-400"
                  >
                    {student.is_active ? "Faolsizlantirish" : "Faollashtirish"}
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <Pagination
            page={page}
            total={total}
            hasPrev={Boolean(data?.previous)}
            hasNext={Boolean(data?.next)}
            onPrev={() => setPage((p) => Math.max(1, p - 1))}
            onNext={() => setPage((p) => p + 1)}
            busy={isFetching}
          />
        </div>
      )}

      {confirmTarget && (
        <ConfirmDialog
          title={confirmTarget.is_active ? "O'quvchini faolsizlantirish" : "O'quvchini faollashtirish"}
          confirmLabel={confirmTarget.is_active ? "Faolsizlantirish" : "Faollashtirish"}
          danger={confirmTarget.is_active}
          loading={toggleActive.isPending}
          onConfirm={() => toggleActive.mutate(confirmTarget)}
          onClose={() => setConfirmTarget(null)}
        >
          <span className="font-medium text-ink capitalize">
            {displayName(confirmTarget).toLocaleLowerCase("uz")}
          </span>{" "}
          {confirmTarget.is_active
            ? "faolsizlantirilsinmi? U tizimga kira olmaydi."
            : "qayta faollashtirilsinmi?"}
        </ConfirmDialog>
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
