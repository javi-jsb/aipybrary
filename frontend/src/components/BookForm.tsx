import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router";
import { createBook, getBook, updateBook } from "../api/books";
import { apiErrorToFormMessage } from "../api/errors";
import type { Book, BookCreate } from "../api/types";
import {
  EMPTY_BOOK_FORM_VALUES,
  generateIsbn13,
  validateBookForm,
  type BookFieldErrors,
  type BookFormValues,
} from "./bookValidation";

function toFormValues(book: Book): BookFormValues {
  return {
    title: book.title,
    author: book.author,
    isbn: book.isbn ?? "",
    publicationYear: book.publication_year !== null ? String(book.publication_year) : "",
    synopsis: book.synopsis ?? "",
  };
}

/** Trim text fields and collapse blanks to `null`, so an edit clears a value
 * rather than sending an empty string the backend would reject. */
function toPayload(values: BookFormValues): BookCreate {
  const isbn = values.isbn.trim();
  const year = values.publicationYear.trim();
  const synopsis = values.synopsis.trim();
  return {
    title: values.title.trim(),
    author: values.author.trim(),
    isbn: isbn === "" ? null : isbn,
    publication_year: year === "" ? null : Number(year),
    synopsis: synopsis === "" ? null : synopsis,
  };
}

const inputClass =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 focus:border-slate-500 focus:outline-none";

/** Input classes, switching to a red border when the field has a validation error. */
function fieldClass(error: string | undefined): string {
  return error
    ? inputClass
        .replace("border-slate-300", "border-red-400")
        .replace("focus:border-slate-500", "focus:border-red-500")
    : inputClass;
}

function FieldError({ id, message }: { id: string; message: string | undefined }) {
  if (!message) return null;
  return (
    <p id={id} role="alert" className="text-sm text-red-600">
      {message}
    </p>
  );
}

interface FieldsProps {
  /** Present in edit mode; drives PATCH vs POST. */
  bookId?: string;
  initial: BookFormValues;
}

function BookFormFields({ bookId, initial }: FieldsProps) {
  const isEdit = bookId !== undefined;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [values, setValues] = useState<BookFormValues>(initial);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<BookFieldErrors>({});

  const mutation = useMutation({
    mutationFn: (payload: BookCreate) =>
      isEdit ? updateBook(bookId, payload) : createBook(payload),
    onSuccess: () => {
      // Refresh the list (and this book's detail) so the change shows on return.
      queryClient.invalidateQueries({ queryKey: ["books"] });
      if (isEdit) queryClient.invalidateQueries({ queryKey: ["book", bookId] });
      navigate("/books");
    },
    onError: (err) => setError(apiErrorToFormMessage(err)),
  });

  function update<K extends keyof BookFormValues>(key: K, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }));
    // Clear a field's error as the user edits it, so stale messages don't linger.
    setFieldErrors((prev) => (prev[key] ? { ...prev, [key]: undefined } : prev));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    // Validate client-side first so invalid input never costs a 422 round-trip.
    const errors = validateBookForm(values);
    if (Object.values(errors).some(Boolean)) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    mutation.mutate(toPayload(values));
  }

  return (
    <section>
      <h1 className="mb-6 text-xl font-semibold text-slate-800">
        {isEdit ? "Edit book" : "New book"}
      </h1>

      <form onSubmit={handleSubmit} noValidate className="max-w-lg space-y-4">
        <div className="space-y-1">
          <label htmlFor="title" className="block text-sm font-medium text-slate-700">
            Title
          </label>
          <input
            id="title"
            value={values.title}
            onChange={(e) => update("title", e.target.value)}
            aria-invalid={fieldErrors.title !== undefined}
            aria-describedby={fieldErrors.title ? "title-error" : undefined}
            className={fieldClass(fieldErrors.title)}
          />
          <FieldError id="title-error" message={fieldErrors.title} />
        </div>

        <div className="space-y-1">
          <label htmlFor="author" className="block text-sm font-medium text-slate-700">
            Author
          </label>
          <input
            id="author"
            value={values.author}
            onChange={(e) => update("author", e.target.value)}
            aria-invalid={fieldErrors.author !== undefined}
            aria-describedby={fieldErrors.author ? "author-error" : undefined}
            className={fieldClass(fieldErrors.author)}
          />
          <FieldError id="author-error" message={fieldErrors.author} />
        </div>

        <div className="space-y-1">
          <label htmlFor="isbn" className="block text-sm font-medium text-slate-700">
            ISBN
          </label>
          <div className="flex items-center gap-2">
            <input
              id="isbn"
              value={values.isbn}
              onChange={(e) => update("isbn", e.target.value)}
              aria-invalid={fieldErrors.isbn !== undefined}
              aria-describedby={fieldErrors.isbn ? "isbn-error" : undefined}
              className={fieldClass(fieldErrors.isbn)}
            />
            {/* Dev-only convenience: hidden in production builds
                (`import.meta.env.DEV` is false there). */}
            {import.meta.env.DEV && (
              <button
                type="button"
                onClick={() => update("isbn", generateIsbn13())}
                className="shrink-0 rounded-md border border-slate-300 px-2.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                title="Fill with a random valid ISBN-13"
              >
                Generate
              </button>
            )}
          </div>
          <FieldError id="isbn-error" message={fieldErrors.isbn} />
        </div>

        <div className="space-y-1">
          <label htmlFor="publicationYear" className="block text-sm font-medium text-slate-700">
            Publication year
          </label>
          <input
            id="publicationYear"
            type="number"
            step="1"
            value={values.publicationYear}
            onChange={(e) => update("publicationYear", e.target.value)}
            aria-invalid={fieldErrors.publicationYear !== undefined}
            aria-describedby={fieldErrors.publicationYear ? "publicationYear-error" : undefined}
            className={fieldClass(fieldErrors.publicationYear)}
          />
          <FieldError id="publicationYear-error" message={fieldErrors.publicationYear} />
        </div>

        <div className="space-y-1">
          <label htmlFor="synopsis" className="block text-sm font-medium text-slate-700">
            Synopsis
          </label>
          <textarea
            id="synopsis"
            rows={4}
            value={values.synopsis}
            onChange={(e) => update("synopsis", e.target.value)}
            className={inputClass}
          />
        </div>

        {error && (
          <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-md bg-slate-800 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? "Saving…" : "Save"}
          </button>
          <Link to="/books" className="text-sm font-medium text-slate-600 hover:text-slate-800">
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}

/**
 * Book create/edit form. In edit mode (`/books/:id/edit`) it fetches the book
 * to prefill the fields; in create mode (`/books/new`) it starts blank. Both
 * submit through `useMutation` over `apiClient` and surface `409`/`422` errors
 * on the form via {@link apiErrorToFormMessage}.
 */
export function BookForm() {
  const { id } = useParams<{ id: string }>();

  const book = useQuery({
    queryKey: ["book", id],
    queryFn: () => getBook(id!),
    enabled: id !== undefined,
  });

  if (id === undefined) {
    return <BookFormFields initial={EMPTY_BOOK_FORM_VALUES} />;
  }

  if (book.isPending) {
    return <p className="text-slate-500">Loading book…</p>;
  }

  if (book.isError) {
    return (
      <p role="alert" className="rounded-md bg-red-50 p-4 text-red-700">
        {apiErrorToFormMessage(book.error, "Failed to load book.")}
      </p>
    );
  }

  // Remount when the loaded book changes so the controlled fields re-seed.
  return (
    <BookFormFields key={book.data.id} bookId={book.data.id} initial={toFormValues(book.data)} />
  );
}
