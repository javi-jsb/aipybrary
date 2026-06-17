import type { MemberStatus } from "../api/types";

const STATUS_CLASS: Record<MemberStatus, string> = {
  active: "bg-emerald-100 text-emerald-700",
  suspended: "bg-amber-100 text-amber-700",
};

/** Small coloured pill rendering a member's status, shared by the list and
 * detail views so the styling stays in one place. */
export function MemberStatusBadge({ status }: { status: MemberStatus }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_CLASS[status]}`}>
      {status}
    </span>
  );
}
