import type { ReactNode } from "react";

import { DangerButton, PrimaryButton, SecondaryButton } from "./form";
import { Modal } from "./Modal";

/**
 * A yes/no confirmation over a `Modal`, so a destructive row action (deactivate
 * a user, delete a subject) takes a deliberate second click instead of firing
 * the moment a link is tapped — easy to do by accident on a phone.
 */
export function ConfirmDialog({
  title,
  children,
  confirmLabel = "Tasdiqlash",
  cancelLabel = "Bekor qilish",
  onConfirm,
  onClose,
  loading = false,
  danger = false,
}: {
  title: string;
  children: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onClose: () => void;
  loading?: boolean;
  danger?: boolean;
}) {
  const Confirm = danger ? DangerButton : PrimaryButton;
  return (
    <Modal title={title} onClose={onClose}>
      <div className="text-sm text-ink-muted">{children}</div>
      <div className="flex justify-end gap-2 pt-4">
        <SecondaryButton type="button" onClick={onClose}>
          {cancelLabel}
        </SecondaryButton>
        <Confirm type="button" loading={loading} onClick={onConfirm}>
          {confirmLabel}
        </Confirm>
      </div>
    </Modal>
  );
}
