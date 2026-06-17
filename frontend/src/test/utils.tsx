import type { ReactElement } from "react";
import { render, type RenderResult } from "@testing-library/react";
import { AuthProvider } from "../auth/AuthProvider";
import type { Book } from "../api/types";

/**
 * Render a component tree wrapped in the real {@link AuthProvider}, so screens
 * that consume `useAuth` (LoginScreen, BooksList, App) work as they do in the
 * app. Auth state derives from the token store; seed it with `setToken` before
 * rendering to start authenticated.
 */
export function renderWithAuth(ui: ReactElement): RenderResult {
  return render(<AuthProvider>{ui}</AuthProvider>);
}

/** Build a JSON `Response`, matching what the backend returns through fetch. */
export function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** A complete `Book`, with fields overridable per test. */
export function makeBook(overrides: Partial<Book> = {}): Book {
  return {
    id: "book-1",
    title: "The Pragmatic Programmer",
    author: "Hunt & Thomas",
    isbn: "9780201616224",
    publication_year: 1999,
    synopsis: null,
    copies_total: 3,
    copies_available: 2,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}
