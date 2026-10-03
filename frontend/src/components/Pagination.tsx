import { SecondaryButton } from "./form";

/**
 * Prev/next pager for a DRF `PageNumberPagination` list. Shows the current
 * slice ("21–40 / 554") and the page position, and disables each arrow when the
 * API reports no page in that direction. Hidden entirely when everything fits
 * on one page.
 */
export function Pagination({
  page,
  total,
  pageSize = 20,
  hasPrev,
  hasNext,
  onPrev,
  onNext,
  busy = false,
}: {
  page: number;
  total: number;
  pageSize?: number;
  hasPrev: boolean;
  hasNext: boolean;
  onPrev: () => void;
  onNext: () => void;
  busy?: boolean;
}) {
  if (total <= pageSize) return null;

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const rangeStart = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const rangeEnd = Math.min(page * pageSize, total);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <p className="text-sm text-ink-muted">
        {rangeStart}–{rangeEnd} / {total}
      </p>
      <div className="flex items-center gap-2">
        <SecondaryButton type="button" disabled={!hasPrev || busy} onClick={onPrev}>
          Oldingi
        </SecondaryButton>
        <span className="text-sm text-ink-muted">
          {page} / {totalPages}
        </span>
        <SecondaryButton type="button" disabled={!hasNext || busy} onClick={onNext}>
          Keyingi
        </SecondaryButton>
      </div>
    </div>
  );
}
