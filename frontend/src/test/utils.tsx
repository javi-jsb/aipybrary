import type { ReactElement } from "react";
import { render, type RenderResult } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router";
import { AuthProvider } from "../auth/AuthProvider";
import type { Book } from "../api/types";

interface RenderOptions {
  /** Initial history stack for the in-memory router (default `["/"]`). */
  initialEntries?: string[];
}

/**
 * Render a component tree wrapped in the providers it gets in the real app: a
 * fresh TanStack Query client, an in-memory router, and the real
 * {@link AuthProvider}. Screens that consume `useAuth`, `useQuery`, or router
 * hooks work as they do in production. Auth state derives from the token store;
 * seed it with `setToken` before rendering to start authenticated.
 *
 * Each call builds its own `QueryClient` (retries off) so cached data never
 * leaks between tests and error states surface immediately.
 */
export function renderWithAuth(
  ui: ReactElement,
  { initialEntries = ["/"] }: RenderOptions = {},
): RenderResult {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <AuthProvider>{ui}</AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
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
