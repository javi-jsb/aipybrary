import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { deleteBook, getBooks } from "../api/books";
import { apiErrorToFormMessage } from "../api/errors";
import type { Book } from "../api/types";
import { useCurrentUser } from "../auth/useCurrentUser";
import { canManageBooks } from "../auth/roles";

interface BookRowProps {
  book: Book;
  canManage: boolean;
}

function BookRow({ book, canManage }: BookRowProps) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const remove = useMutation({
    mutationFn: () => deleteBook(book.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["books"] }),
  });

  return (
    <li className="rounded-lg bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium text-slate-900">{book.title}</p>
          <p className="text-sm text-slate-600">{book.author}</p>
          {book.publication_year !== null && (
            <p className="text-xs text-slate-400">{book.publication_year}</p>
          )}
        </div>

        {canManage && (
          <div className="flex shrink-0 items-center gap-2">
            <Link
              to={`/books/${book.id}/edit`}
              className="rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Edit
            </Link>
            {confirming ? (
              <>
                <button
                  type="button"
                  onClick={() => remove.mutate()}
                  disabled={remove.isPending}
                  className="rounded-md bg-red-600 px-2.5 py-1 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
                >
                  {remove.isPending ? "Deleting…" : "Confirm"}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  disabled={remove.isPending}
                  className="rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => setConfirming(true)}
                className="rounded-md border border-red-300 px-2.5 py-1 text-sm font-medium text-red-700 hover:bg-red-50"
              >
                Delete
              </button>
            )}
          </div>
        )}
      </div>

      {remove.isError && (
        <p role="alert" className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {apiErrorToFormMessage(remove.error, "Failed to delete the book.")}
        </p>
      )}
    </li>
  );
}

export function BooksList() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ["books"],
    queryFn: getBooks,
  });
  const currentUser = useCurrentUser();
  const canManage = canManageBooks(currentUser.data?.role);

  return (
    <section>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-800">Books</h1>
        {canManage && (
          <Link
            to="/books/new"
            className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
          >
            New book
          </Link>
        )}
      </div>

      {isPending && <p className="text-slate-500">Loading books…</p>}

      {isError && (
        <p role="alert" className="rounded-md bg-red-50 p-4 text-red-700">
          {apiErrorToFormMessage(error, "Failed to load books.")}
        </p>
      )}

      {data &&
        (data.items.length === 0 ? (
          <p className="text-slate-500">No books found.</p>
        ) : (
          <ul className="space-y-3">
            {data.items.map((book) => (
              <BookRow key={book.id} book={book} canManage={canManage} />
            ))}
          </ul>
        ))}
    </section>
  );
}
