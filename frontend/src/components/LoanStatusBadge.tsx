import type { LoanStatus } from "../api/types";

const STATUS_CLASS: Record<LoanStatus, string> = {
  active: "bg-sky-100 text-sky-700",
  overdue: "bg-red-100 text-red-700",
  returned: "bg-slate-100 text-slate-600",
};

/** Small coloured pill rendering a loan's status, so the styling stays in one
 * place if the loans view grows more surfaces. */
export function LoanStatusBadge({ status }: { status: LoanStatus }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASS[status]}`}>
      {status}
    </span>
  );
}
