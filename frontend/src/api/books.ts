import { apiClient } from "./client";
import type { BookListResponse } from "./types";

/** GET /books — requires a valid bearer token (attached by apiClient). */
export function getBooks(): Promise<BookListResponse> {
  return apiClient<BookListResponse>("/books");
}
