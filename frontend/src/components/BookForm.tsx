import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router";
import { createBook, getBook, updateBook } from "../api/books";
import { apiErrorToFormMessage } from "../api/errors";
import type { Book, BookCreate } from "../api/types";

interface FormValues {
  title: string;
  author: string;
  isbn: string;
  publicationYear: string;
  synopsis: string;
}

const EMPTY_VALUES: FormValues = {
  title: "",
  author: "",
  isbn: "",
  publicationYear: "",
  synopsis: "",
};

function toFormValues(book: Book): FormValues {
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
function toPayload(values: FormValues): BookCreate {
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

interface FieldsProps {
  /** Present in edit mode; drives PATCH vs POST. */
  bookId?: string;
  initial: FormValues;
}

function BookFormFields({ bookId, initial }: FieldsProps) {
  const isEdit = bookId !== undefined;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [values, setValues] = useState<FormValues>(initial);
  const [error, setError] = useState<string | null>(null);

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

  function update<K extends keyof FormValues>(key: K, value: string) {
    setValues((prev) => ({ ...prev, [key]: value }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    mutation.mutate(toPayload(values));
  }

  return (
    <section>
      <h1 className="mb-6 text-xl font-semibold text-slate-800">
        {isEdit ? "Edit book" : "New book"}
      </h1>

      <form onSubmit={handleSubmit} className="max-w-lg space-y-4">
        <div className="space-y-1">
          <label htmlFor="title" className="block text-sm font-medium text-slate-700">
            Title
          </label>
          <input
            id="title"
            required
            value={values.title}
            onChange={(e) => update("title", e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="author" className="block text-sm font-medium text-slate-700">
            Author
          </label>
          <input
            id="author"
            required
            value={values.author}
            onChange={(e) => update("author", e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="isbn" className="block text-sm font-medium text-slate-700">
            ISBN
          </label>
          <input
            id="isbn"
            value={values.isbn}
            onChange={(e) => update("isbn", e.target.value)}
            className={inputClass}
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="publicationYear" className="block text-sm font-medium text-slate-700">
            Publication year
          </label>
          <input
            id="publicationYear"
            type="number"
            value={values.publicationYear}
            onChange={(e) => update("publicationYear", e.target.value)}
            className={inputClass}
          />
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
    return <BookFormFields initial={EMPTY_VALUES} />;
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
