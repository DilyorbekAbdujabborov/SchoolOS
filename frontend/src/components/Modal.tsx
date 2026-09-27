import { useEffect } from "react";
import { X } from "lucide-react";
import type { ReactNode } from "react";

/**
 * A centred dialog on a scrim. The panel enters with a short scale-and-lift,
 * the scrim fades — both fast, so it feels responsive rather than theatrical.
 * Escape and a scrim click both close it, and the page behind stops scrolling
 * while it's open.
 */
export function Modal({
  title,
  description,
  onClose,
  children,
  footer,
  size = "md",
}: {
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previous;
    };
  }, [onClose]);

  const width = size === "sm" ? "max-w-sm" : size === "lg" ? "max-w-2xl" : "max-w-md";

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <button
        aria-label="Yopish"
        onClick={onClose}
        className="absolute inset-0 animate-fade bg-slate-950/45 backdrop-blur-[2px] dark:bg-black/70"
      />
      <div
        className={`pop relative flex max-h-[92vh] w-full ${width} flex-col overflow-hidden rounded-t-2xl border border-line bg-surface shadow-pop sm:rounded-2xl`}
      >
        <div className="flex items-start justify-between gap-4 border-b border-line-soft px-5 py-4">
          <div className="min-w-0">
            <h2 className="text-base font-bold tracking-tight text-ink">{title}</h2>
            {description && <p className="mt-0.5 text-xs text-ink-subtle">{description}</p>}
          </div>
          <button onClick={onClose} aria-label="Yopish" className="btn-icon -mr-1.5 -mt-1">
            <X size={17} />
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4">{children}</div>

        {footer && (
          <div className="flex items-center justify-end gap-2 border-t border-line-soft bg-surface-raised px-5 py-3.5">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
