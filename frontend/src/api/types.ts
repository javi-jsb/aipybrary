// Hand-written mirrors of the backend payloads. These are maintained manually
// for now; generating them from the API's OpenAPI schema is a future iteration.

export interface Book {
  id: string;
  title: string;
  author: string;
  isbn: string | null;
  publication_year: number | null;
  synopsis: string | null;
  copies_total: number;
  copies_available: number;
  created_at: string;
  updated_at: string;
}

/** Payload for `POST /books`. `isbn`/`publication_year`/`synopsis` are optional
 * server-side; we always send them (as `null` when blank) so an edit can clear
 * a previously set value. */
export interface BookCreate {
  title: string;
  author: string;
  isbn: string | null;
  publication_year: number | null;
  synopsis: string | null;
}

/** Payload for `PATCH /books/{id}` — every field is optional. */
export type BookUpdate = Partial<BookCreate>;

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export type BookListResponse = PaginatedResponse<Book>;

export type MemberStatus = "active" | "suspended";

export interface Member {
  id: string;
  full_name: string;
  email: string;
  status: MemberStatus;
  created_at: string;
  updated_at: string;
}

/** Payload for `POST /members`. The backend provisions a linked `member`-role
 * user and returns the one-time `initial_password` (see `MemberCreateResponse`). */
export interface MemberCreate {
  full_name: string;
  email: string;
  status: MemberStatus;
}

/** Payload for `PATCH /members/{id}`. Email is owned by the linked user and is
 * not editable here, so only `full_name` and `status` can change. */
export interface MemberUpdate {
  full_name?: string;
  status?: MemberStatus;
}

/** Response of `POST /members` — a `Member` plus the one-time initial password,
 * which is returned exactly once and never again on subsequent reads. */
export interface MemberCreateResponse extends Member {
  initial_password: string;
}

export type MemberListResponse = PaginatedResponse<Member>;

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export type UserRole = "admin" | "staff" | "member";

/** Mirror of the backend `UserPublic` payload returned by `GET /auth/me`. */
export interface User {
  id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
