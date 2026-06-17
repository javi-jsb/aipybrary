import { apiClient } from "./client";
import type { User } from "./types";

/** GET /auth/me — resolves the authenticated caller (requires a bearer token). */
export function getCurrentUser(): Promise<User> {
  return apiClient<User>("/auth/me");
}
