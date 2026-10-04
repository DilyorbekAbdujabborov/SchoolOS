import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Users } from "lucide-react";
import { useState } from "react";

import { Badge } from "../../components/Badge";
import { Field, Input, PrimaryButton, SecondaryButton, Select } from "../../components/form";
import { Modal } from "../../components/Modal";
import { PageHeader } from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import type { Paginated, Teacher, TeacherTaskCategory, TeacherTaskSummary } from "../../types";

const CATEGORY_OPTIONS: { value: TeacherTaskCategory; label: string }[] = [
  { value: "ADMINISTRATIVE", label: "Ma'muriy" },
  { value: "REPORT", label: "Hisobot" },
  { value: "MEETING", label: "Yig'ilish" },
  { value: "OTHER", label: "Boshqa" },
];

interface TaskFormState {
  title: string;
  description: string;
  category: TeacherTaskCategory;
  recipient: "one" | "all";
  teacher: string;
}

const EMPTY_FORM: TaskFormState = {
  title: "",
  description: "",
  category: "ADMINISTRATIVE",
  recipient: "one",
  teacher: "",
};

export function DirectorTasksPage() {
  const queryClient = useQueryClient();
  const [isModalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState<TaskFormState>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const { data: teachers } = useQuery({
    queryKey: ["teachers"],
    queryFn: async () => (await api.get<Paginated<Teacher>>("/app/teachers/")).data,
  });

  const { data: tasks, isLoading, isError } = useQuery({
    queryKey: ["teacher-tasks"],
    queryFn: async () => (await api.get<Paginated<TeacherTaskSummary>>("/app/teacher-tasks/")).data,
  });

  const createTask = useMutation({
    mutationFn: async (payload: TaskFormState) =>
      api.post("/app/teacher-tasks/", {
        title: payload.title,
        description: payload.description,
        category: payload.category,
        send_to_all: payload.recipient === "all",
        teacher: payload.recipient === "one" ? Number(payload.teacher) : null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teacher-tasks"] });
      setModalOpen(false);
      setForm(EMPTY_FORM);
      setError(null);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setError(detail ? Object.values(detail).flat().join(" ") : "Saqlashda xatolik.");
    },
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Vazifa berish"
        action={<PrimaryButton onClick={() => setModalOpen(true)}>+ Vazifa berish</PrimaryButton>}
      />

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {tasks && tasks.results.length === 0 && (
        <EmptyState title="Hali vazifa yubormagansiz" description="O'qituvchilarga ma'muriy vazifa yuborish uchun yuqoridagi tugmani bosing." />
      )}

      {tasks && tasks.results.length > 0 && (
        <div className="space-y-3">
          {tasks.results.map((task) => (
            <div key={task.id} className="card p-5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-slate-900 dark:text-slate-50">{task.title}</p>
                  {task.description && (
                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{task.description}</p>
                  )}
                </div>
                <Badge tone="brand">{task.category_display}</Badge>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span className="inline-flex items-center gap-1">
                  <Users size={13} />
                  {task.is_broadcast ? "Hammasiga" : "1 ta o'qituvchiga"}
                </span>
                <span>·</span>
                <span>
                  {task.done_count} / {task.assignee_count} bajardi
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {isModalOpen && (
        <Modal title="Yangi vazifa" onClose={() => setModalOpen(false)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              createTask.mutate(form);
            }}
            className="space-y-4"
          >
            <Field label="Sarlavha">
              <Input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
            </Field>
            <Field label="Tavsif">
              <Input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </Field>
            <Field label="Kategoriya">
              <Select
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value as TeacherTaskCategory })}
              >
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </Field>

            <div className="space-y-2">
              <span className="block text-sm font-medium text-slate-700 dark:text-slate-300">Kimga</span>
              <div className="flex gap-4 text-sm text-slate-700 dark:text-slate-300">
                <label className="flex items-center gap-1.5">
                  <input
                    type="radio"
                    name="recipient"
                    checked={form.recipient === "one"}
                    onChange={() => setForm({ ...form, recipient: "one" })}
                  />
                  Bitta o'qituvchi
                </label>
                <label className="flex items-center gap-1.5">
                  <input
                    type="radio"
                    name="recipient"
                    checked={form.recipient === "all"}
                    onChange={() => setForm({ ...form, recipient: "all" })}
                  />
                  Hammasiga
                </label>
              </div>
              {form.recipient === "one" && (
                <Select
                  required
                  value={form.teacher}
                  onChange={(e) => setForm({ ...form, teacher: e.target.value })}
                >
                  <option value="">— o'qituvchini tanlang —</option>
                  {teachers?.results.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.first_name || teacher.last_name
                        ? `${teacher.first_name} ${teacher.last_name}`.trim()
                        : `O'qituvchi №${teacher.id}`}
                    </option>
                  ))}
                </Select>
              )}
            </div>

            {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <SecondaryButton type="button" onClick={() => setModalOpen(false)}>
                Bekor qilish
              </SecondaryButton>
              <PrimaryButton type="submit" disabled={createTask.isPending}>
                {createTask.isPending ? "Yuborilmoqda..." : "Yuborish"}
              </PrimaryButton>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
