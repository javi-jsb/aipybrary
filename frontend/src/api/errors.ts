import { ApiError } from "./client";

/**
 * Map a thrown error into a message suitable for a form-level alert.
 *
 * `apiClient` already unwraps the backend `detail` into {@link ApiError.message},
 * so validation (`422`) and conflict (`409`) responses surface their server
 * message verbatim. Anything that is not an {@link ApiError} (a network failure,
 * an unexpected throw) collapses to a generic fallback so internal details never
 * leak onto the form.
 */
export function apiErrorToFormMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again.",
): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return fallback;
}
