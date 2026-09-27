import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  LabelHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

/**
 * Form controls and buttons.
 *
 * Buttons are *not* all blue. The hierarchy is: one `PrimaryButton` per view
 * (blue, the thing you came here to do), `SecondaryButton` beside it (neutral,
 * an alternative), `DangerButton` only for things that destroy, and `Ghost`
 * for the third level of chrome. Everything shares the `.btn` geometry so a
 * row of mixed buttons still lines up.
 *
 * `loading` swaps the label for a spinner and disables the control, so no
 * button ever sits in an ambiguous "did it work?" state.
 */

export const inputClass = "field-input";

export function Field({
  label,
  hint,
  children,
  className = "",
  ...rest
}: {
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
} & LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label className={`block ${className}`} {...rest}>
      <span className="mb-1.5 block text-sm font-medium text-ink-muted">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-ink-subtle">{hint}</span>}
    </label>
  );
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={className ? `${inputClass} ${className}` : inputClass} />;
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select {...props} className={`${inputClass} ${className ?? ""} cursor-pointer pr-8`} />
  );
}

export function Textarea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={`${inputClass} ${className ?? ""} min-h-[92px] resize-y`} />;
}

type Variant = "primary" | "secondary" | "success" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

const SIZE_CLASS: Record<Size, string> = {
  sm: "btn-sm",
  md: "btn-md",
  lg: "btn-lg",
};

const VARIANT_CLASS: Record<Variant, string> = {
  primary: "btn-primary",
  secondary: "btn-secondary",
  success: "btn-success",
  danger: "btn-danger",
  ghost: "btn-ghost",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  /** Shows a spinner, disables the button and marks it busy for a11y. */
  loading?: boolean;
  /** Stretches the button to its container — for form submits. */
  block?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  block = false,
  className = "",
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`btn ${SIZE_CLASS[size]} ${VARIANT_CLASS[variant]} ${block ? "w-full" : ""} ${
        className
      }`}
    >
      {loading && <span className="spinner" />}
      {children}
    </button>
  );
}

export function PrimaryButton(props: Omit<ButtonProps, "variant">) {
  return <Button variant="primary" {...props} />;
}

export function SecondaryButton(props: Omit<ButtonProps, "variant">) {
  return <Button variant="secondary" {...props} />;
}

export function SuccessButton(props: Omit<ButtonProps, "variant">) {
  return <Button variant="success" {...props} />;
}

export function DangerButton(props: Omit<ButtonProps, "variant">) {
  return <Button variant="danger" {...props} />;
}

export function GhostButton(props: Omit<ButtonProps, "variant">) {
  return <Button variant="ghost" {...props} />;
}

/** Square icon button, for toolbars, card corners and table row actions. */
export function IconButton({
  label,
  children,
  className = "",
  tone,
  ...props
}: Omit<ButtonProps, "children" | "size"> & {
  label: string;
  children: ReactNode;
  tone?: "default" | "danger";
}) {
  return (
    <button
      {...props}
      aria-label={label}
      title={label}
      className={`btn-icon ${
        tone === "danger" ? "hover:bg-rose-500/10 hover:text-rose-600 dark:hover:text-rose-400" : ""
      } ${className}`}
    >
      {children}
    </button>
  );
}

/** Segmented control for switching a view between 2–4 options. */
export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className = "",
}: {
  options: { value: T; label: ReactNode }[];
  value: T;
  onChange: (value: T) => void;
  className?: string;
}) {
  return (
    <div className={`inline-flex rounded-lg border border-line bg-surface-raised p-0.5 ${className}`}>
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            aria-pressed={active}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150 ${
              active
                ? "bg-surface text-ink shadow-card"
                : "text-ink-muted hover:text-ink"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
