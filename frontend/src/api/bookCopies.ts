import { apiClient } from "./client";
import type { BookCopyCreate, BookCopyListResponse, BookCopy } from "./types";

const JSON_HEADERS = { "Content-Type": "application/json" };

// The backend caps `size` at 100; a single book is not expected to exceed that,
// so we request the max in one page rather than paginating the copies view.
const COPIES_PAGE_SIZE = 100;

/** GET /book-copies?book_id=… — the copies belonging to one book. */
export function getBookCopies(bookId: string): Promise<BookCopyListResponse> {
  const query = new URLSearchParams({ book_id: bookId, size: String(COPIES_PAGE_SIZE) });
  return apiClient<BookCopyListResponse>(`/book-copies?${query.toString()}`);
}

/** GET /book-copies/{id} — a single copy, used to resolve a loan's copy to its
 * barcode and owning book in the loans view. */
export function getBookCopy(id: string): Promise<BookCopy> {
  return apiClient<BookCopy>(`/book-copies/${id}`);
}

/** POST /book-copies — add a copy (201). Throws `ApiError` 409 on a duplicate
 * barcode, 422 when `book_id` does not reference an existing book. */
export function createBookCopy(data: BookCopyCreate): Promise<BookCopy> {
  return apiClient<BookCopy>("/book-copies", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  });
}

/** DELETE /book-copies/{id} — 204 on success. */
export function deleteBookCopy(id: string): Promise<void> {
  return apiClient<void>(`/book-copies/${id}`, { method: "DELETE" });
}
