import { apiClient } from "./client";
import type { LoginRequest, LoginResponse } from "./types";

/**
 * POST /auth/login — the endpoint expects OAuth2 form credentials
 * (application/x-www-form-urlencoded), not JSON.
 */
export function login(credentials: LoginRequest): Promise<LoginResponse> {
  const body = new URLSearchParams();
  body.set("username", credentials.username);
  body.set("password", credentials.password);

  return apiClient<LoginResponse>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
}
