// Client-side mirror of the backend's member validation (MemberCreate), so the
// form rejects bad input before issuing a request the API would answer with a
// 422. The email rule matches `validate_email` in `app/core/validators.py`
// (trim + lowercase, then `^[^@\s]+@[^@\s]+\.[^@\s]+$`); the full_name length
// matches `MemberCreate.full_name` (max 300).

import type { MemberStatus } from "../api/types";

export interface MemberFormValues {
  fullName: string;
  email: string;
  status: MemberStatus;
}

export const EMPTY_MEMBER_FORM_VALUES: MemberFormValues = {
  fullName: "",
  email: "",
  status: "active",
};

export type MemberFieldErrors = Partial<Record<keyof MemberFormValues, string>>;

const FULL_NAME_MAX = 300;
const EMAIL_MAX = 320;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** Validate an email the way the backend does (after trim + lowercase). Returns
 * an error message, or `null` when valid. */
export function validateEmail(raw: string): string | null {
  const normalized = raw.trim().toLowerCase();
  if (normalized === "") return "Email is required.";
  if (normalized.length > EMAIL_MAX) {
    return `Email must be at most ${EMAIL_MAX} characters.`;
  }
  if (!EMAIL_RE.test(normalized)) return "Invalid email format.";
  return null;
}

/** Per-field validation for the member form. An empty map means the values are
 * safe to submit. Email is only validated on create (it is not editable on
 * update, where it is owned by the linked user). */
export function validateMemberForm(
  values: MemberFormValues,
  { isEdit }: { isEdit: boolean },
): MemberFieldErrors {
  const errors: MemberFieldErrors = {};

  const fullName = values.fullName.trim();
  if (fullName === "") errors.fullName = "Full name is required.";
  else if (fullName.length > FULL_NAME_MAX) {
    errors.fullName = `Full name must be at most ${FULL_NAME_MAX} characters.`;
  }

  if (!isEdit) {
    const emailError = validateEmail(values.email);
    if (emailError) errors.email = emailError;
  }

  return errors;
}
