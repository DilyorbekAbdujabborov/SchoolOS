import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Circle } from "lucide-react";

import { Badge } from "../../components/Badge";
import { SecondaryButton } from "../../components/form";
import { PageHeader } from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { api } from "../../lib/api";
import type { Paginated, TeacherTaskAssignment } from "../../types";

export function TeacherTasksPage() {
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["my-tasks"],
    queryFn: async () => (await api.get<Paginated<TeacherTaskAssignment>>("/my-tasks/")).data,
  });

  const markDone = useMutation({
    mutationFn: async (id: number) => api.patch(`/my-tasks/${id}/mark-done/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["my-tasks"] }),
  });

  return (
    <div className="space-y-6">
      <PageHeader title="Vazifalarim" />

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {data && data.results.length === 0 && <EmptyState title="Hozircha vazifa yo'q" />}

      {data && data.results.length > 0 && (
        <div className="space-y-3">
          {data.results.map((assignment) => (
            <div
              key={assignment.id}
              className="card p-5"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  {assignment.is_done ? (
                    <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
                  ) : (
                    <Circle className="mt-0.5 h-5 w-5 shrink-0 text-slate-300 dark:text-slate-600" />
                  )}
                  <div>
                    <p className="font-semibold text-slate-900 dark:text-slate-50">{assignment.title}</p>
                    {assignment.description && (
                      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{assignment.description}</p>
                    )}
                    <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                      {assignment.created_by_name} · {new Date(assignment.created_at).toLocaleDateString("uz-UZ")}
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge tone="brand">{assignment.category_display}</Badge>
                  {!assignment.is_done && (
                    <SecondaryButton onClick={() => markDone.mutate(assignment.id)} disabled={markDone.isPending}>
                      Bajarildi
                    </SecondaryButton>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
