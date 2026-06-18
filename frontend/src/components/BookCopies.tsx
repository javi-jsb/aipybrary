import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router";
import { getBook } from "../api/books";
import { createBookCopy, deleteBookCopy, getBookCopies } from "../api/bookCopies";
import { apiErrorToFormMessage } from "../api/errors";
import type { BookCopy } from "../api/types";
import { useCurrentUser } from "../auth/useCurrentUser";
import { canManageCopies } from "../auth/roles";

const inputClass =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 focus:border-slate-500 focus:outline-none";

// Mirror the backend column limits (book_copy_model.py) so over-long input is
// caught before it costs a 422 round-trip. A duplicate barcode (409) is not
// knowable client-side and still surfaces from the server.
const BARCODE_MAX = 100;
const LOCATION_MAX = 200;

interface AddCopyFormProps {
  bookId: string;
}

function AddCopyForm({ bookId }: AddCopyFormProps) {
  const queryClient = useQueryClient();
  const [barcode, setBarcode] = useState("");
  const [location, setLocation] = useState("");
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);

  const add = useMutation({
    mutationFn: () =>
      createBookCopy({
        book_id: bookId,
        barcode: barcode.trim(),
        location: location.trim() || null,
        notes: null,
      }),
    onSuccess: () => {
      // The new copy bumps the book's availability, so refresh the copies view
      // plus the book detail and the books list that show those counts.
      queryClient.invalidateQueries({ queryKey: ["copies", bookId] });
      queryClient.invalidateQueries({ queryKey: ["book", bookId] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
      setBarcode("");
      setLocation("");
    },
    onError: (err) => setError(apiErrorToFormMessage(err)),
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    const trimmed = barcode.trim();
    if (!trimmed) {
      setFieldError("Barcode is required.");
      return;
    }
    if (trimmed.length > BARCODE_MAX) {
      setFieldError(`Barcode must be at most ${BARCODE_MAX} characters.`);
      return;
    }
    if (location.trim().length > LOCATION_MAX) {
      setFieldError(`Location must be at most ${LOCATION_MAX} characters.`);
      return;
    }
    setFieldError(undefined);
    add.mutate();
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="rounded-lg bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 space-y-1">
          <label htmlFor="barcode" className="block text-sm font-medium text-slate-700">
            Barcode
          </label>
          <input
            id="barcode"
            value={barcode}
            onChange={(e) => {
              setBarcode(e.target.value);
              if (fieldError) setFieldError(undefined);
            }}
            aria-invalid={fieldError !== undefined}
            aria-describedby={fieldError ? "barcode-error" : undefined}
            className={
              fieldError
                ? inputClass
                    .replace("border-slate-300", "border-red-400")
                    .replace("focus:border-slate-500", "focus:border-red-500")
                : inputClass
            }
          />
        </div>
        <div className="flex-1 space-y-1">
          <label htmlFor="location" className="block text-sm font-medium text-slate-700">
            Location <span className="text-slate-400">(optional)</span>
          </label>
          <input
            id="location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            className={inputClass}
          />
        </div>
        <button
          type="submit"
          disabled={add.isPending}
          className="rounded-md bg-slate-800 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {add.isPending ? "Adding…" : "Add copy"}
        </button>
      </div>

      {fieldError && (
        <p id="barcode-error" role="alert" className="mt-2 text-sm text-red-600">
          {fieldError}
        </p>
      )}
      {error && (
        <p role="alert" className="mt-2 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}
    </form>
  );
}

interface CopyRowProps {
  copy: BookCopy;
  bookId: string;
  canManage: boolean;
}

function CopyRow({ copy, bookId, canManage }: CopyRowProps) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const remove = useMutation({
    mutationFn: () => deleteBookCopy(copy.id),
    onSuccess: () => {
      // Removing a copy lowers the book's availability — refresh the same keys
      // the add action does.
      queryClient.invalidateQueries({ queryKey: ["copies", bookId] });
      queryClient.invalidateQueries({ queryKey: ["book", bookId] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
    },
  });

  return (
    <li className="rounded-lg bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-slate-900">{copy.barcode}</p>
          {copy.location !== null && <p className="text-sm text-slate-600">{copy.location}</p>}
        </div>

        {canManage &&
          (confirming ? (
            <div className="flex shrink-0 items-center gap-2">
              <button
                type="button"
                onClick={() => remove.mutate()}
                disabled={remove.isPending}
                className="rounded-md bg-red-600 px-2.5 py-1 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
              >
                {remove.isPending ? "Removing…" : "Confirm"}
              </button>
              <button
                type="button"
                onClick={() => setConfirming(false)}
                disabled={remove.isPending}
                className="rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setConfirming(true)}
              className="shrink-0 rounded-md border border-red-300 px-2.5 py-1 text-sm font-medium text-red-700 hover:bg-red-50"
            >
              Remove
            </button>
          ))}
      </div>

      {remove.isError && (
        <p role="alert" className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {apiErrorToFormMessage(remove.error, "Failed to remove the copy.")}
        </p>
      )}
    </li>
  );
}

/**
 * Copies view for a single book (`/books/:id/copies`): lists the book's copies
 * and, for roles that may manage them, an inline add form and per-copy remove
 * action. Add/remove invalidate the copies, the book detail, and the books list
 * so the availability counts stay in sync. Viewing is open to any authenticated
 * user; the controls are role-gated (UX-only — see `roles.ts`).
 */
export function BookCopies() {
  const { id } = useParams<{ id: string }>();
  const currentUser = useCurrentUser();
  const canManage = canManageCopies(currentUser.data?.role);

  const book = useQuery({
    queryKey: ["book", id],
    queryFn: () => getBook(id!),
    enabled: id !== undefined,
  });

  const copies = useQuery({
    queryKey: ["copies", id],
    queryFn: () => getBookCopies(id!),
    enabled: id !== undefined,
  });

  return (
    <section>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-slate-800">
          {book.data ? `Copies of “${book.data.title}”` : "Copies"}
        </h1>
        {book.data && (
          <p className="text-sm text-slate-500">
            {book.data.copies_available} of {book.data.copies_total} available
          </p>
        )}
      </div>

      {canManage && id !== undefined && (
        <div className="mb-6">
          <AddCopyForm bookId={id} />
        </div>
      )}

      {copies.isPending && <p className="text-slate-500">Loading copies…</p>}

      {copies.isError && (
        <p role="alert" className="rounded-md bg-red-50 p-4 text-red-700">
          {apiErrorToFormMessage(copies.error, "Failed to load copies.")}
        </p>
      )}

      {copies.data &&
        (copies.data.items.length === 0 ? (
          <p className="text-slate-500">No copies yet.</p>
        ) : (
          <ul className="space-y-3">
            {copies.data.items.map((copy) => (
              <CopyRow key={copy.id} copy={copy} bookId={id!} canManage={canManage} />
            ))}
          </ul>
        ))}

      <Link
        to="/books"
        className="mt-6 inline-block text-sm font-medium text-slate-600 hover:text-slate-800"
      >
        Back to books
      </Link>
    </section>
  );
}
