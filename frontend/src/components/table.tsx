import type { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from "react";

/**
 * Data tables.
 *
 * The head is a raised well with small caps-ish labels, rows are separated by
 * the softest possible line, and the whole thing scrolls horizontally inside
 * its own rounded card rather than blowing out the page layout. Row hover is
 * a neutral wash — never a colour, so a table of statuses keeps its colour
 * budget for the status column.
 */
export function Table({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`card overflow-hidden ${className}`}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-left text-sm">{children}</table>
      </div>
    </div>
  );
}

export function Thead({ children }: { children: React.ReactNode }) {
  return (
    <thead className="border-b border-line bg-surface-raised text-ink-subtle">{children}</thead>
  );
}

export function Tbody({ children }: { children: React.ReactNode }) {
  return <tbody className="divide-y divide-line-soft">{children}</tbody>;
}

export function Tr({ children, className, ...rest }: HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={`transition-colors duration-150 hover:bg-surface-raised/70 ${className ?? ""}`}
      {...rest}
    >
      {children}
    </tr>
  );
}

export function Th({ children, className, ...rest }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={`whitespace-nowrap px-4 py-2.5 text-[11px] font-semibold uppercase tracking-[0.06em] ${
        className ?? ""
      }`}
      {...rest}
    >
      {children}
    </th>
  );
}

export function Td({ children, className, ...rest }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={`px-4 py-3 align-middle text-ink-muted ${className ?? ""}`} {...rest}>
      {children}
    </td>
  );
}

/** The emphasised cell in a row — a name, a number worth reading first. */
export function TdStrong({ children, className, ...rest }: TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={`px-4 py-3 align-middle font-medium text-ink ${className ?? ""}`} {...rest}>
      {children}
    </td>
  );
}
