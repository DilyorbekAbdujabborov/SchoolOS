import { useEffect, type ReactNode } from "react";

import { GameAnswerFeedback, GameInlineError, GameOptionButton, GameQuestionCard } from "./GameUI";
import type { useLiveGame } from "./useLiveGame";

/** Everything under a live-key game's stage: loading/error states, the
 * current question card (slides in per question, shakes on a wrong answer),
 * and the after-answer feedback — identical across Minora qurish, Kodni
 * buzish and Xazina ovi, only the label and success detail differ. */
export function LiveQuestionSection({
  game,
  label,
  successDetail,
  wrongTitle,
  explanationLabel,
  stacked = false,
}: {
  game: ReturnType<typeof useLiveGame>;
  /** One option per row on large screens — for a narrow side column. */
  stacked?: boolean;
  /** Small eyebrow above the question, e.g. "3-SEGMENT", "CHALLENGE 03". */
  label?: ReactNode;
  successDetail?: ReactNode;
  wrongTitle?: string;
  explanationLabel?: string;
}) {
  const { question, questionIndex, feedback, questionsQuery } = game;

  // Keyboard play: 1–4 or A–D picks an option (the next-question button takes
  // focus on its own after a wrong answer, so Enter continues).
  useEffect(() => {
    if (!question || feedback) return;
    function onKey(event: KeyboardEvent) {
      if (event.ctrlKey || event.metaKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      const key = event.key.toLowerCase();
      const index = "1234".includes(key) && key !== "" ? Number(key) - 1 : "abcd".indexOf(key);
      if (index >= 0 && index < (question?.options.length ?? 0)) {
        event.preventDefault();
        game.answer(index);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [question, feedback, game]);

  return (
    <>
      {questionsQuery.isLoading && (
        <p className="py-6 text-center text-sm text-slate-500 dark:text-slate-400">O'yin tayyorlanmoqda...</p>
      )}
      {questionsQuery.isError && (
        <GameInlineError>Savollar hozircha tayyor emas. Birozdan so'ng qayta urinib ko'ring.</GameInlineError>
      )}

      {question && (
        <div key={questionIndex} className="animate-pop-in">
          <div className={feedback && !feedback.result.correct ? "animate-shake" : undefined}>
            <GameQuestionCard>
              {label && (
                <p className="text-xs font-semibold uppercase tracking-wider text-brand-600 dark:text-brand-400">
                  {label}
                </p>
              )}
              <p
                className={`text-base font-semibold text-slate-900 dark:text-slate-50 sm:text-lg ${label ? "mt-1" : ""}`}
              >
                {question.text}
              </p>
              <div className={`mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2 ${stacked ? "lg:grid-cols-1" : ""}`}>
                {question.options.map((option, i) => (
                  <GameOptionButton
                    key={`${i}-${option}`}
                    index={i}
                    text={option}
                    state={game.optionState(i)}
                    disabled={Boolean(feedback) || game.answerPending}
                    onClick={() => game.answer(i)}
                  />
                ))}
              </div>
            </GameQuestionCard>
          </div>
        </div>
      )}

      {game.answerError && (
        <p className="text-center text-xs font-medium text-red-600 dark:text-red-400">
          Javob yuborilmadi. Internetni tekshirib, variantni qayta tanlang.
        </p>
      )}

      {feedback && (
        <GameAnswerFeedback
          correct={feedback.result.correct}
          xpGained={feedback.xpGained}
          successDetail={successDetail}
          wrongTitle={wrongTitle}
          explanationLabel={explanationLabel}
          correctAnswerText={question?.options[feedback.result.correct_index]}
          explanation={feedback.result.explanation}
          isLast={game.isLastQuestion}
          onNext={game.goNext}
        />
      )}
    </>
  );
}
