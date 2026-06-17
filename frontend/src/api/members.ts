import { apiClient } from "./client";
import type {
  Member,
  MemberCreate,
  MemberCreateResponse,
  MemberListResponse,
  MemberUpdate,
} from "./types";

const JSON_HEADERS = { "Content-Type": "application/json" };

/** GET /members — requires a valid bearer token (attached by apiClient). */
export function getMembers(): Promise<MemberListResponse> {
  return apiClient<MemberListResponse>("/members");
}

/** GET /members/{id} — a single member, used for the detail and edit views. */
export function getMember(id: string): Promise<Member> {
  return apiClient<Member>(`/members/${id}`);
}

/** POST /members — create a member (201). Returns the one-time `initial_password`.
 * Throws `ApiError` 409 on a duplicate email. */
export function createMember(data: MemberCreate): Promise<MemberCreateResponse> {
  return apiClient<MemberCreateResponse>("/members", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  });
}

/** PATCH /members/{id} — partial update of `full_name`/`status`. */
export function updateMember(id: string, data: MemberUpdate): Promise<Member> {
  return apiClient<Member>(`/members/${id}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  });
}

/** DELETE /members/{id} — 204 on success. Throws `ApiError` 409 when the member
 * still has loans (the backend's `loans.member_id` FK is ON DELETE RESTRICT). */
export function deleteMember(id: string): Promise<void> {
  return apiClient<void>(`/members/${id}`, { method: "DELETE" });
}
