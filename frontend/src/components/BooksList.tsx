import { useQuery } from "@tanstack/react-query";
import { apiErrorToFormMessage } from "../api/errors";
import { getBooks } from "../api/books";

export function BooksList() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ["books"],
    queryFn: getBooks,
  });

  return (
    <section>
      <h1 className="mb-6 text-xl font-semibold text-slate-800">Books</h1>

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
    </section>
  );
}
