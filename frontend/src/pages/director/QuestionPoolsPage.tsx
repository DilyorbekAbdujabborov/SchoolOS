import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ClipboardCheck, Copy, Database, Download, Sparkles } from "lucide-react";
import { useState } from "react";

import { Badge } from "../../components/Badge";
import { Field, Input, PrimaryButton, SecondaryButton, Select, Textarea } from "../../components/form";
import { PageHeader } from "../../components/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/states";
import { Table, Tbody, Td, Th, Thead, Tr } from "../../components/table";
import { api } from "../../lib/api";
import type { Paginated, QuestionPoolStatus, SchoolClass, Subject } from "../../types";

// Mirrors the backend's POOL_LOW_THRESHOLD (apps.games.services) — below this,
// the scheduled auto-refill will top the pool back up on its own.
const POOL_LOW_THRESHOLD = 20;

function poolTone(count: number): "amber" | "emerald" {
  return count < POOL_LOW_THRESHOLD ? "amber" : "emerald";
}

export function QuestionPoolsPage() {
  const queryClient = useQueryClient();
  const [subject, setSubject] = useState("");
  const [schoolClass, setSchoolClass] = useState("");
  const [lastResult, setLastResult] = useState<string | null>(null);

  // External-chatbot flow: copy the prompt, generate elsewhere, paste the JSON back.
  const [count, setCount] = useState("30");
  const [promptText, setPromptText] = useState("");
  const [copied, setCopied] = useState(false);
  const [pasteContent, setPasteContent] = useState("");
  const [importResult, setImportResult] = useState<string | null>(null);

  const { data: subjects } = useQuery({
    queryKey: ["subjects"],
    queryFn: async () => (await api.get<Paginated<Subject>>("/subjects/")).data,
  });
  const { data: classes } = useQuery({
    queryKey: ["classes"],
    queryFn: async () => (await api.get<Paginated<SchoolClass>>("/classes/")).data,
  });

  const { data: pools, isLoading, isError } = useQuery({
    queryKey: ["question-pools"],
    queryFn: async () => (await api.get<QuestionPoolStatus[]>("/question-pools/")).data,
  });

  // The subject+class payload shared by refill / prompt / import. Class is
  // optional for prompt & import (a subject-wide bank); refill requires it.
  function poolPayload(extra: Record<string, unknown> = {}) {
    const body: Record<string, unknown> = { subject: Number(subject), ...extra };
    if (schoolClass) body.school_class = Number(schoolClass);
    return body;
  }

  const refill = useMutation({
    mutationFn: async () =>
      (await api.post<{ added: number }>("/question-pools/refill/", poolPayload())).data,
    onSuccess: ({ added }) => {
      queryClient.invalidateQueries({ queryKey: ["question-pools"] });
      setLastResult(
        added > 0
          ? `${added} ta savol qo'shildi.`
          : "AI hozircha savol yarata olmadi — birozdan so'ng qayta urinib ko'ring.",
      );
    },
  });

  const copyPrompt = useMutation({
    mutationFn: async () => {
      const body = poolPayload({ count: Math.max(1, Math.min(200, Number(count) || 30)) });
      return (await api.post<{ prompt: string }>("/question-pools/prompt/", body)).data;
    },
    onSuccess: async ({ prompt }) => {
      setPromptText(prompt);
      setCopied(false);
      try {
        await navigator.clipboard.writeText(prompt);
        setCopied(true);
      } catch {
        // Clipboard blocked (permissions/insecure context) — the prompt is shown
        // below for manual copy, so this is not an error worth surfacing.
      }
    },
  });

  const importQuestions = useMutation({
    mutationFn: async () =>
      (
        await api.post<{ received: number; added: number }>(
          "/question-pools/import/",
          poolPayload({ content: pasteContent }),
        )
      ).data,
    onSuccess: ({ received, added }) => {
      queryClient.invalidateQueries({ queryKey: ["question-pools"] });
      setImportResult(`${added} ta savol qo'shildi (${received} ta qabul qilindi).`);
      if (added > 0) setPasteContent("");
    },
    onError: () => setImportResult("JSON o'qib bo'lmadi — chatbot bergan javobni to'liq nusxalab joylang."),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        icon={Database}
        title="Savollar ombori"
        subtitle={
          'Barcha o\'yinlar ("Arqon tortish", "Viktorina", "Minora qurish", "Kodni buzish", "Xazina ovi", "Jang maydoni", "Tower Defense", "Neon Racing") shu yerdagi tayyor savollardan foydalanadi — o\'yin boshlanganda AI\'ga jonli so\'rov yubormaydi. Har bir sinf + fan uchun alohida ombor bor.'
        }
      />

      <div className="flex flex-wrap items-end gap-3 card p-5">
        <Field label="Sinf">
          <Select value={schoolClass} onChange={(e) => setSchoolClass(e.target.value)} className="min-w-[160px]">
            <option value="">— tanlang —</option>
            {classes?.results.map((cls) => (
              <option key={cls.id} value={cls.id}>
                {cls.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Fan">
          <Select value={subject} onChange={(e) => setSubject(e.target.value)} className="min-w-[160px]">
            <option value="">— tanlang —</option>
            {subjects?.results.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <PrimaryButton
          onClick={() => {
            setLastResult(null);
            refill.mutate();
          }}
          disabled={!subject || !schoolClass || refill.isPending}
          className="flex items-center gap-1.5"
        >
          <Sparkles size={15} />
          {refill.isPending ? "Tayyorlanmoqda..." : "Pool'ni to'ldirish"}
        </PrimaryButton>
        {lastResult && <p className="w-full text-sm text-slate-500 dark:text-slate-400">{lastResult}</p>}
      </div>

      {/* External chatbot flow: copy the prompt, generate in ChatGPT/Claude, paste back. */}
      <div className="card space-y-4 p-5">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
            AI'dan tashqarida tayyorlash (ChatGPT / Claude)
          </h3>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Yuqoridan fan (va xohlasangiz sinf) tanlang. 1) Promptni nusxalang → 2) ChatGPT yoki Claude'ga
            joylang → 3) chiqgan JSON javobni pastki maydonga joylab, import qiling.
          </p>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <Field label="Savollar soni">
            <Input
              type="number"
              min={1}
              max={200}
              value={count}
              onChange={(e) => setCount(e.target.value)}
              className="w-28"
            />
          </Field>
          <SecondaryButton
            onClick={() => copyPrompt.mutate()}
            disabled={!subject || copyPrompt.isPending}
            className="flex items-center gap-1.5"
          >
            {copied ? <ClipboardCheck size={15} /> : <Copy size={15} />}
            {copyPrompt.isPending ? "Tayyorlanmoqda..." : copied ? "Nusxalandi" : "Promptni nusxalash"}
          </SecondaryButton>
        </div>

        {promptText && (
          <Textarea
            readOnly
            value={promptText}
            rows={6}
            onFocus={(e) => e.currentTarget.select()}
            className="font-mono text-xs"
          />
        )}

        <Field label="Chatbot javobini (JSON) shu yerga joylang">
          <Textarea
            value={pasteContent}
            onChange={(e) => setPasteContent(e.target.value)}
            rows={6}
            placeholder='{"questions": [{"text": "...", "options": ["...","...","...","..."], "correct_index": 0, "explanation": "..."}]}'
            className="font-mono text-xs"
          />
        </Field>
        <div className="flex flex-wrap items-center gap-3">
          <PrimaryButton
            onClick={() => {
              setImportResult(null);
              importQuestions.mutate();
            }}
            disabled={!subject || !pasteContent.trim() || importQuestions.isPending}
            className="flex items-center gap-1.5"
          >
            <Download size={15} />
            {importQuestions.isPending ? "Import qilinmoqda..." : "Import qilish"}
          </PrimaryButton>
          {importResult && <p className="text-sm text-slate-500 dark:text-slate-400">{importResult}</p>}
        </div>
      </div>

      {isLoading && <LoadingState />}
      {isError && <ErrorState />}
      {pools && pools.length === 0 && (
        <EmptyState
          title="Hali birorta pool to'ldirilmagan"
          description="Yuqoridan sinf va fan tanlab, birinchi marta to'ldiring."
        />
      )}
      {pools && pools.length > 0 && (
        <Table>
          <Thead>
            <Tr>
              <Th>Sinf</Th>
              <Th>Fan</Th>
              <Th className="text-right">Savollar soni</Th>
            </Tr>
          </Thead>
          <Tbody>
            {pools.map((pool) => (
              <Tr key={`${pool.subject}-${pool.school_class}`}>
                <Td className="font-medium text-slate-900 dark:text-slate-50">{pool.school_class_name}</Td>
                <Td className="text-slate-600 dark:text-slate-300">{pool.subject_name}</Td>
                <Td className="text-right">
                  <Badge tone={poolTone(pool.count)}>{pool.count} ta</Badge>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </div>
  );
}
