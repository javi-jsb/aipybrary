import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router";
import { borrowLoan, getLoans } from "../api/loans";
import { getMembers } from "../api/members";
import { getBooks } from "../api/books";
import { getBookCopies } from "../api/bookCopies";
import { apiErrorToFormMessage } from "../api/errors";
import type { LoanCreate } from "../api/types";

const selectClass =
  "w-full rounded-md border border-slate-300 px-3 py-2 text-slate-900 focus:border-slate-500 focus:outline-none disabled:bg-slate-50 disabled:text-slate-400";

/**
 * Borrow form (`/loans/new`): pick a member and an available copy, then create
 * the loan. Copies already on an active loan are filtered out client-side (the
 * backend still enforces it with a 409). On success it invalidates loans and the
 * affected book's availability, then returns to the loans list.
 */
export function LoanForm() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [memberId, setMemberId] = useState("");
  const [bookId, setBookId] = useState("");
  const [copyId, setCopyId] = useState("");
  const [fieldError, setFieldError] = useState<string | undefined>();
  const [error, setError] = useState<string | null>(null);

  const members = useQuery({ queryKey: ["members"], queryFn: getMembers });
  const books = useQuery({ queryKey: ["books"], queryFn: getBooks });
  const loans = useQuery({ queryKey: ["loans"], queryFn: getLoans });
  const copies = useQuery({
    queryKey: ["copies", bookId],
    queryFn: () => getBookCopies(bookId),
    enabled: bookId !== "",
  });

  // Suspended members are rejected by the backend (422), so only offer active ones.
  const activeMembers = useMemo(
    () => (members.data?.items ?? []).filter((m) => m.status === "active"),
    [members.data],
  );

  // A copy is unavailable while it has a loan that has not been returned.
  const onLoanCopyIds = useMemo(() => {
    const ids = new Set<string>();
    for (const loan of loans.data?.items ?? []) {
      if (loan.returned_at === null) ids.add(loan.book_copy_id);
    }
    return ids;
  }, [loans.data]);

  const availableCopies = useMemo(
    () => (copies.data?.items ?? []).filter((c) => !onLoanCopyIds.has(c.id)),
    [copies.data, onLoanCopyIds],
  );

  const borrow = useMutation({
    mutationFn: (data: LoanCreate) => borrowLoan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["loans"] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
      queryClient.invalidateQueries({ queryKey: ["book", bookId] });
      queryClient.invalidateQueries({ queryKey: ["copies", bookId] });
      navigate("/loans");
    },
    onError: (err) => setError(apiErrorToFormMessage(err)),
  });

  function handleBookChange(value: string) {
    setBookId(value);
    // The previously chosen copy belongs to the old book — reset it.
    setCopyId("");
    if (fieldError) setFieldError(undefined);
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!memberId) {
      setFieldError("Select a member.");
      return;
    }
    if (!copyId) {
      setFieldError("Select an available copy.");
      return;
    }
    setFieldError(undefined);
    borrow.mutate({ member_id: memberId, book_copy_id: copyId });
  }

  return (
    <section>
      <h1 className="mb-6 text-xl font-semibold text-slate-800">New loan</h1>

      <form
        onSubmit={handleSubmit}
        noValidate
        className="space-y-4 rounded-lg bg-white p-6 shadow-sm"
      >
        <div className="space-y-1">
          <label htmlFor="member" className="block text-sm font-medium text-slate-700">
            Member
          </label>
          <select
            id="member"
            value={memberId}
            onChange={(e) => {
              setMemberId(e.target.value);
              if (fieldError) setFieldError(undefined);
            }}
            className={selectClass}
          >
            <option value="">Select a member…</option>
            {activeMembers.map((member) => (
              <option key={member.id} value={member.id}>
                {member.full_name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label htmlFor="book" className="block text-sm font-medium text-slate-700">
            Book
          </label>
          <select
            id="book"
            value={bookId}
            onChange={(e) => handleBookChange(e.target.value)}
            className={selectClass}
          >
            <option value="">Select a book…</option>
            {(books.data?.items ?? []).map((book) => (
              <option key={book.id} value={book.id}>
                {book.title}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label htmlFor="copy" className="block text-sm font-medium text-slate-700">
            Available copy
          </label>
          <select
            id="copy"
            value={copyId}
            onChange={(e) => {
              setCopyId(e.target.value);
              if (fieldError) setFieldError(undefined);
            }}
            disabled={bookId === "" || copies.isPending}
            className={selectClass}
          >
            <option value="">
              {bookId === ""
                ? "Select a book first…"
                : availableCopies.length === 0
                  ? "No available copies"
                  : "Select a copy…"}
            </option>
            {availableCopies.map((copy) => (
              <option key={copy.id} value={copy.id}>
                {copy.barcode}
                {copy.location ? ` (${copy.location})` : ""}
              </option>
            ))}
          </select>
        </div>

        {fieldError && (
          <p role="alert" className="text-sm text-red-600">
            {fieldError}
          </p>
        )}
        {error && (
          <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={borrow.isPending}
            className="rounded-md bg-slate-800 px-4 py-2 font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {borrow.isPending ? "Borrowing…" : "Borrow"}
          </button>
          <Link to="/loans" className="text-sm font-medium text-slate-600 hover:text-slate-800">
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}
