import { apiClient } from "./client";
import type { Loan, LoanCreate, LoanListResponse } from "./types";

const JSON_HEADERS = { "Content-Type": "application/json" };

// The backend caps `size` at 100. The exercise dataset is not expected to exceed
// that, so we request the max in one page rather than paginating the loans view.
const LOANS_PAGE_SIZE = 100;

/** GET /loans — the loans list, newest first (the backend default sort). */
export function getLoans(): Promise<LoanListResponse> {
  const query = new URLSearchParams({ size: String(LOANS_PAGE_SIZE) });
  return apiClient<LoanListResponse>(`/loans?${query.toString()}`);
}

/** POST /loans — borrow a copy for a member (201). Throws `ApiError`: 404 when
 * the member or copy is unknown, 409 when the copy is already on loan, 422 when
 * the member is suspended or has reached the active-loan limit. */
export function borrowLoan(data: LoanCreate): Promise<Loan> {
  return apiClient<Loan>("/loans", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(data),
  });
}

/** POST /loans/{id}/return — mark a loan returned. Throws `ApiError` 409 when
 * the loan is already returned. */
export function returnLoan(id: string): Promise<Loan> {
  return apiClient<Loan>(`/loans/${id}/return`, { method: "POST" });
}
