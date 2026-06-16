import { useEffect, useState } from "react";
import { getBooks } from "../api/books";
import type { Book } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type BooksState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; books: Book[] };

export function BooksList() {
  const { logout } = useAuth();
  const [state, setState] = useState<BooksState>({ status: "loading" });

  useEffect(() => {
    let active = true;
    getBooks()
      .then((response) => {
        if (active) setState({ status: "success", books: response.items });
      })
      .catch((err: unknown) => {
        if (active) {
          setState({
            status: "error",
            message: err instanceof Error ? err.message : "Failed to load books.",
          });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
        <h1 className="text-xl font-semibold text-slate-800">Books</h1>
        <button
          type="button"
          onClick={logout}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Sign out
        </button>
      </header>

      <main className="mx-auto max-w-3xl p-6">
        {state.status === "loading" && <p className="text-slate-500">Loading books…</p>}

        {state.status === "error" && (
          <p role="alert" className="rounded-md bg-red-50 p-4 text-red-700">
            {state.message}
          </p>
        )}

        {state.status === "success" &&
          (state.books.length === 0 ? (
            <p className="text-slate-500">No books found.</p>
          ) : (
            <ul className="space-y-3">
              {state.books.map((book) => (
                <li key={book.id} className="rounded-lg bg-white p-4 shadow-sm">
                  <p className="font-medium text-slate-900">{book.title}</p>
                  <p className="text-sm text-slate-600">{book.author}</p>
                  {book.publication_year !== null && (
                    <p className="text-xs text-slate-400">{book.publication_year}</p>
                  )}
                </li>
              ))}
            </ul>
          ))}
      </main>
    </div>
  );
}
