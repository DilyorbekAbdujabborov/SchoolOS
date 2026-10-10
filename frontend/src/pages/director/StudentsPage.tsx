import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

import { Avatar } from "../../components/Avatar";
import { Badge } from "../../components/Badge";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { Field, Input, PrimaryButton, Select, SecondaryButton, Textarea } from "../../components/form";
import { Modal } from "../../components/Modal";
import { PageHeader } from "../../components/PageHeader";
import { Pagination } from "../../components/Pagination";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { Table, Tbody, Td, Th, Thead, Tr } from "../../components/table";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { can } from "../../lib/capabilities";
import type { Gender, Paginated, SchoolClass, Student } from "../../types";

interface StudentFormState {
  email: string;
  first_name: string;
  last_name: string;
  middle_name: string;
  gender: Gender;
  birth_date: string;
  pinfl: string;
  passport_number: string;
  phone_number: string;
  parent_phone_number: string;
  region: string;
  address: string;
  school_class: string;
  password: string;
}

const EMPTY_FORM: StudentFormState = {
  email: "",
  first_name: "",
  last_name: "",
  middle_name: "",
  gender: "",
  birth_date: "",
  pinfl: "",
  passport_number: "",
  phone_number: "",
  parent_phone_number: "",
  region: "",
  address: "",
  school_class: "",
  password: "",
};

const GENDER_LABEL: Record<Exclude<Gender, "">, string> = {
  male: "Erkak",
  female: "Ayol",
};

function displayName(student: Student): string {
  return `${student.first_name} ${student.last_name}`.trim();
}

/** The full three-part name, as it reads on a document. */
function fullLegalName(student: Student): string {
  return [student.last_name, student.first_name, student.middle_name].filter(Boolean).join(" ").trim();
}

function formatBirthDate(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("uz-UZ", { day: "2-digit", month: "long", year: "numeric" });
}

export function StudentsPage() {
  const { user } = useAuth();
  const canCreate = can(user, "students.create");
  const canUpdate = can(user, "students.update");
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
  const [detailTarget, setDetailTarget] = useState<Student | null>(null);

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
        await api.get<Paginated<Student>>("/students/", {
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
        await api.post("/students/", {
          ...payload,
          school_class: payload.school_class ? Number(payload.school_class) : null,
          birth_date: payload.birth_date || null,
        })
      ).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
      queryClient.invalidateQueries({ queryKey: ["classes"] });
      setModalOpen(false);
      setForm(EMPTY_FORM);
      setError(null);
    },
    onError: () => setError("Saqlashda xatolik. Email yoki PINFL band bo'lishi mumkin."),
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
  const isFiltering = debouncedSearch !== "" || classFilter !== "" || statusFilter !== "";
  const students = data?.results ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="O'quvchilar"
        subtitle={total > 0 ? `Jami ${total} ta o'quvchi` : undefined}
        action={
          canCreate ? (
            <PrimaryButton onClick={() => setModalOpen(true)}>+ O'quvchi qo'shish</PrimaryButton>
          ) : undefined
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          type="search"
          placeholder="Ism, email yoki PINFL bo'yicha qidirish..."
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
                      <button
                        type="button"
                        onClick={() => setDetailTarget(student)}
                        className="group flex items-center gap-3 text-left"
                      >
                        <Avatar name={displayName(student)} size={36} />
                        <div className="min-w-0">
                          <p className="truncate font-medium capitalize text-slate-900 decoration-brand-400/50 underline-offset-2 group-hover:underline dark:text-slate-50">
                            {displayName(student).toLocaleLowerCase("uz")}
                          </p>
                          <p className="truncate text-xs text-ink-muted">{student.email}</p>
                        </div>
                      </button>
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
                      {canUpdate && (
                        <button
                          onClick={() => setConfirmTarget(student)}
                          className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
                        >
                          {student.is_active ? "Faolsizlantirish" : "Faollashtirish"}
                        </button>
                      )}
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
                <button
                  type="button"
                  onClick={() => setDetailTarget(student)}
                  className="flex w-full items-start gap-3 text-left"
                >
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
                </button>
                <div className="flex items-center justify-between gap-2 text-sm">
                  <span className="text-ink-muted">
                    {student.school_class_name ?? "Sinfsiz"} ·{" "}
                    <span className="font-medium text-amber-600 dark:text-amber-400">
                      {student.total_xp.toLocaleString("uz-UZ")} XP
                    </span>
                  </span>
                  {canUpdate && (
                    <button
                      onClick={() => setConfirmTarget(student)}
                      className="shrink-0 font-medium text-brand-600 hover:underline dark:text-brand-400"
                    >
                      {student.is_active ? "Faolsizlantirish" : "Faollashtirish"}
                    </button>
                  )}
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

      {detailTarget && (
        <StudentDetail student={detailTarget} onClose={() => setDetailTarget(null)} />
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
        <Modal
          title="O'quvchi qo'shish"
          description="Hisob ma'lumotlari majburiy; shaxsiy ma'lumotlarni keyin ham to'ldirsa bo'ladi."
          size="lg"
          onClose={() => setModalOpen(false)}
        >
          <form onSubmit={handleSubmit} className="space-y-6">
            <fieldset className="space-y-3">
              <legend className="text-xs font-semibold uppercase tracking-wider text-ink-subtle">
                Hisob
              </legend>
              <Field label="Email">
                <Input
                  type="email"
                  required
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </Field>
              <Field label="Vaqtinchalik parol" hint="Kamida 8 ta belgi. O'quvchi birinchi kirishda o'zgartiradi.">
                <Input
                  type="password"
                  required
                  minLength={8}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
              </Field>
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="text-xs font-semibold uppercase tracking-wider text-ink-subtle">
                Shaxsiy ma'lumotlar
              </legend>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Familiya">
                  <Input
                    value={form.last_name}
                    onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  />
                </Field>
                <Field label="Ism">
                  <Input
                    value={form.first_name}
                    onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  />
                </Field>
              </div>
              <Field label="Otasining ismi">
                <Input
                  value={form.middle_name}
                  onChange={(e) => setForm({ ...form, middle_name: e.target.value })}
                />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Jinsi">
                  <Select
                    value={form.gender}
                    onChange={(e) => setForm({ ...form, gender: e.target.value as Gender })}
                  >
                    <option value="">— tanlanmagan —</option>
                    <option value="male">Erkak</option>
                    <option value="female">Ayol</option>
                  </Select>
                </Field>
                <Field label="Tug'ilgan sana">
                  <Input
                    type="date"
                    value={form.birth_date}
                    onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
                  />
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Field label="PINFL" hint="14 ta raqam">
                  <Input
                    inputMode="numeric"
                    maxLength={14}
                    value={form.pinfl}
                    onChange={(e) => setForm({ ...form, pinfl: e.target.value.replace(/\D/g, "") })}
                  />
                </Field>
                <Field label="Passport">
                  <Input
                    value={form.passport_number}
                    onChange={(e) => setForm({ ...form, passport_number: e.target.value })}
                  />
                </Field>
              </div>
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="text-xs font-semibold uppercase tracking-wider text-ink-subtle">
                Aloqa va manzil
              </legend>
              <div className="grid grid-cols-2 gap-3">
                <Field label="Telefon">
                  <Input
                    type="tel"
                    value={form.phone_number}
                    onChange={(e) => setForm({ ...form, phone_number: e.target.value })}
                  />
                </Field>
                <Field label="Ota-ona telefoni">
                  <Input
                    type="tel"
                    value={form.parent_phone_number}
                    onChange={(e) => setForm({ ...form, parent_phone_number: e.target.value })}
                  />
                </Field>
              </div>
              <Field label="Viloyat / tuman">
                <Input
                  value={form.region}
                  onChange={(e) => setForm({ ...form, region: e.target.value })}
                />
              </Field>
              <Field label="Manzil">
                <Textarea
                  rows={2}
                  value={form.address}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                />
              </Field>
            </fieldset>

            <fieldset className="space-y-3">
              <legend className="text-xs font-semibold uppercase tracking-wider text-ink-subtle">
                Ta'lim
              </legend>
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
            </fieldset>

            {error && <p className="text-sm font-medium text-red-600 dark:text-red-400">{error}</p>}
            <div className="flex justify-end gap-2 pt-1">
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

/** Read-only profile for one student — the full record behind a table row. */
function StudentDetail({ student, onClose }: { student: Student; onClose: () => void }) {
  const rows: { label: string; value: string | null }[] = [
    { label: "To'liq ism", value: fullLegalName(student) || null },
    { label: "Jinsi", value: student.gender ? GENDER_LABEL[student.gender] : null },
    { label: "Tug'ilgan sana", value: formatBirthDate(student.birth_date) },
    { label: "PINFL", value: student.pinfl },
    { label: "Passport", value: student.passport_number || null },
    { label: "Telefon", value: student.phone_number || null },
    { label: "Ota-ona telefoni", value: student.parent_phone_number || null },
    { label: "Viloyat / tuman", value: student.region || null },
    { label: "Manzil", value: student.address || null },
    { label: "Sinf", value: student.school_class_name },
  ];

  return (
    <Modal title={displayName(student)} description={student.email} size="lg" onClose={onClose}>
      <div className="space-y-5">
        <div className="flex items-center gap-4">
          <Avatar name={displayName(student)} size={56} />
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={student.is_active ? "emerald" : "slate"}>
              {student.is_active ? "Faol" : "Faol emas"}
            </Badge>
            <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:text-amber-300">
              {student.total_xp.toLocaleString("uz-UZ")} XP
            </span>
          </div>
        </div>

        <dl className="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-2">
          {rows.map((row) => (
            <div key={row.label} className="border-b border-line-soft pb-2">
              <dt className="text-xs font-medium text-ink-subtle">{row.label}</dt>
              <dd className="mt-0.5 text-sm text-ink">
                {row.value ?? <span className="text-ink-subtle">—</span>}
              </dd>
            </div>
          ))}
        </dl>

        <div className="flex justify-end border-t border-line-soft pt-4">
          <Link to={`/app/director/users/${student.user_id}`} className="btn btn-primary btn-md">
            To'liq profil sahifasi <ArrowUpRight size={16} />
          </Link>
        </div>
      </div>
    </Modal>
  );
}
