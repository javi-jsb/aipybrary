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

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export type BookListResponse = PaginatedResponse<Book>;

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
