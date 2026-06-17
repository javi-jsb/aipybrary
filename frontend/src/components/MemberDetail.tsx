import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";
import { getMember } from "../api/members";
import { apiErrorToFormMessage } from "../api/errors";
import { useCurrentUser } from "../auth/useCurrentUser";
import { canManageMembers } from "../auth/roles";
import { MemberStatusBadge } from "./MemberStatusBadge";

export function MemberDetail() {
  const { id } = useParams<{ id: string }>();
  const currentUser = useCurrentUser();
  const canManage = canManageMembers(currentUser.data?.role);

  const member = useQuery({
    queryKey: ["member", id],
    queryFn: () => getMember(id!),
    enabled: id !== undefined,
  });

  if (member.isPending) {
    return <p className="text-slate-500">Loading member…</p>;
  }

  if (member.isError) {
    return (
      <p role="alert" className="rounded-md bg-red-50 p-4 text-red-700">
        {apiErrorToFormMessage(member.error, "Failed to load member.")}
      </p>
    );
  }

  const { full_name, email, status } = member.data;

  return (
    <section>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-800">{full_name}</h1>
        {canManage && (
          <Link
            to={`/members/${member.data.id}/edit`}
            className="rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Edit
          </Link>
        )}
      </div>

      <dl className="space-y-4 rounded-lg bg-white p-4 shadow-sm">
        <div>
          <dt className="text-xs font-medium uppercase text-slate-400">Email</dt>
          <dd className="text-slate-900">{email}</dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase text-slate-400">Status</dt>
          <dd className="mt-1">
            <MemberStatusBadge status={status} />
          </dd>
        </div>
      </dl>

      <Link
        to="/members"
        className="mt-6 inline-block text-sm font-medium text-slate-600 hover:text-slate-800"
      >
        Back to members
      </Link>
    </section>
  );
}
