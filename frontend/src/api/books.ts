import { apiClient } from "./client";
import type { Book, BookCreate, BookListResponse, BookUpdate } from "./types";

const JSON_HEADERS = { "Content-Type": "application/json" };

/** GET /books — requires a valid bearer token (attached by apiClient). */
export function getBooks(): Promise<BookListResponse> {
  return apiClient<BookListResponse>("/books");
}

/** GET /books/{id} — a single book, used to prefill the edit form. */
export function getBook(id: string): Promise<Book> {
  return apiClient<Book>(`/books/${id}`);
}

/** POST /books — create a book (201). Throws `ApiError` 409 on duplicate ISBN. */
export function createBook(data: BookCreate): Promise<Book> {
  return apiClient<Book>("/books", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  });
}

/** PATCH /books/{id} — partial update. Throws `ApiError` 409 on duplicate ISBN. */
export function updateBook(id: string, data: BookUpdate): Promise<Book> {
  return apiClient<Book>(`/books/${id}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  });
}

/** DELETE /books/{id} — 204 on success. Throws `ApiError` 409 when the book
 * still has copies. */
export function deleteBook(id: string): Promise<void> {
  return apiClient<void>(`/books/${id}`, { method: "DELETE" });
}
