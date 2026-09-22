/** Extracts the leading grade number from a class name like "9-A" -> 9. Used
 * wherever a director-facing view offers a "6-sinflar / 7-sinflar / ..."
 * filter, so every such filter reads class names the same way. */
export function gradeNumber(className: string): number | null {
  const match = className.match(/^(\d+)/);
  return match ? Number(match[1]) : null;
}

/** Every distinct grade number present across a set of class names, sorted
 * ascending — the options for a grade-level filter. */
export function distinctGrades(classNames: string[]): number[] {
  return Array.from(new Set(classNames.map(gradeNumber).filter((g): g is number => g !== null))).sort(
    (a, b) => a - b,
  );
}
