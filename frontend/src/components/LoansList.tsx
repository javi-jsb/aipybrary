import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { getLoans, returnLoan } from "../api/loans";
import { getMembers } from "../api/members";
import { getBooks } from "../api/books";
import { getBookCopy } from "../api/bookCopies";
import { apiErrorToFormMessage } from "../api/errors";
import type { Loan } from "../api/types";
import { useCurrentUser } from "../auth/useCurrentUser";
import { canManageLoans, canViewMembers } from "../auth/roles";
import { LoanStatusBadge } from "./LoanStatusBadge";

/** Format an ISO timestamp as a plain local date (the loans view only cares
 * about the day, not the time). */
function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

interface LoanRowProps {
  loan: Loan;
  memberName: string | undefined;
  bookTitles: Record<string, string>;
  canManage: boolean;
}

function LoanRow({ loan, memberName, bookTitles, canManage }: LoanRowProps) {
  const queryClient = useQueryClient();

  // The loan only carries a copy id; resolve it to a barcode and owning book so
  // the row reads in human terms. Cached under ["copy", id] and deduped across
  // rows by TanStack Query.
  const copy = useQuery({
    queryKey: ["copy", loan.book_copy_id],
    queryFn: () => getBookCopy(loan.book_copy_id),
  });

  const back = useMutation({
    mutationFn: () => returnLoan(loan.id),
    onSuccess: () => {
      // Returning frees the copy, so availability counts change: refresh the
      // loans list plus the books list/detail and the copies view.
      queryClient.invalidateQueries({ queryKey: ["loans"] });
      queryClient.invalidateQueries({ queryKey: ["books"] });
      if (copy.data) {
        queryClient.invalidateQueries({ queryKey: ["book", copy.data.book_id] });
        queryClient.invalidateQueries({ queryKey: ["copies", copy.data.book_id] });
      }
    },
  });

  const bookTitle = copy.data ? bookTitles[copy.data.book_id] : undefined;
  const isReturned = loan.returned_at !== null;

  return (
    <li className="rounded-lg bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="font-medium text-slate-900">{memberName ?? loan.member_id}</p>
          <p className="text-sm text-slate-600">
            <span className="font-mono">{copy.data?.barcode ?? loan.book_copy_id}</span>
            {bookTitle && <span className="text-slate-500"> · {bookTitle}</span>}
          </p>
          <p className="text-xs text-slate-500">
            {isReturned
              ? `Returned ${formatDate(loan.returned_at!)}`
              : `Due ${formatDate(loan.due_date)}`}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <LoanStatusBadge status={loan.status} />
          {canManage && !isReturned && (
            <button
              type="button"
              onClick={() => back.mutate()}
              disabled={back.isPending}
              className="rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              {back.isPending ? "Returning…" : "Return"}
            </button>
          )}
        </div>
      </div>

      {back.isError && (
        <p role="alert" className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {apiErrorToFormMessage(back.error, "Failed to return the loan.")}
        </p>
      )}
    </li>
  );
}

/**
 * Loans view (`/loans`): lists loans newest-first, resolving each loan's member
 * and copy/book to readable names, with a role-gated return action. Any
 * authenticated user may view; the borrow/return controls are gated (UX-only —
 * see `roles.ts`).
 */
export function LoansList() {
  const currentUser = useCurrentUser();
  const role = currentUser.data?.role;
  const canManage = canManageLoans(role);
  // A `member` is scoped server-side to their own loans (the API forces
  // `member_id == self`) and may not list members — so skip the members fetch
  // (it would `403`) and label each row with the caller's own email instead.
  const canSeeMembers = canViewMembers(role);

  const loans = useQuery({ queryKey: ["loans"], queryFn: getLoans });
  const members = useQuery({
    queryKey: ["members"],
    queryFn: getMembers,
    enabled: canSeeMembers,
  });
  const books = useQuery({ queryKey: ["books"], queryFn: getBooks });

  const memberNames = useMemo(() => {
    const map: Record<string, string> = {};
    for (const member of members.data?.items ?? []) map[member.id] = member.full_name;
    return map;
  }, [members.data]);

  // For a member, every listed loan is their own, so their email reads better
  // than the bare member id when no members listing is available to resolve names.
  const selfLabel = canSeeMembers ? undefined : currentUser.data?.email;

  const bookTitles = useMemo(() => {
    const map: Record<string, string> = {};
    for (const book of books.data?.items ?? []) map[book.id] = book.title;
    return map;
  }, [books.data]);

  return (
    <section>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-800">Loans</h1>
        {canManage && (
          <Link
            to="/loans/new"
            className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
          >
            New loan
          </Link>
        )}
      </div>

      {loans.isPending && <p className="text-slate-500">Loading loans…</p>}

      {loans.isError && (
        <p role="alert" className="rounded-md bg-red-50 p-4 text-red-700">
          {apiErrorToFormMessage(loans.error, "Failed to load loans.")}
        </p>
      )}

      {loans.data &&
        (loans.data.items.length === 0 ? (
          <p className="text-slate-500">No loans yet.</p>
        ) : (
          <ul className="space-y-3">
            {loans.data.items.map((loan) => (
              <LoanRow
                key={loan.id}
                loan={loan}
                memberName={memberNames[loan.member_id] ?? selfLabel}
                bookTitles={bookTitles}
                canManage={canManage}
              />
            ))}
          </ul>
        ))}
    </section>
  );
}
