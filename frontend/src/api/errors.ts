import { ApiError } from "./client";

/** Friendly message for a `403 Forbidden` — the role lacks permission. Shown in
 * place of the raw backend detail so the wording stays user-facing. */
export const FORBIDDEN_MESSAGE = "You don't have permission to do this.";

/** Whether the error is an authenticated-but-unauthorized response (`403`). */
export function isForbiddenError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 403;
}

/** Whether the error is an unauthenticated response (`401`) — a missing,
 * invalid, or expired token, i.e. a session problem, distinct from a `403`. */
export function isUnauthorizedError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

/**
 * Map a thrown error into a message suitable for a form-level alert.
 *
 * `apiClient` already unwraps the backend `detail` into {@link ApiError.message},
 * so validation (`422`) and conflict (`409`) responses surface their server
 * message verbatim. A `403` collapses to the friendly {@link FORBIDDEN_MESSAGE}
 * (the role can't do this), distinct from the session/auth `401` path. Anything
 * that is not an {@link ApiError} (a network failure, an unexpected throw)
 * collapses to a generic fallback so internal details never leak onto the form.
 */
export function apiErrorToFormMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (isForbiddenError(error)) {
    return FORBIDDEN_MESSAGE;
  }
  if (error instanceof ApiError) {
    return error.message;
  }
  return fallback;
}
