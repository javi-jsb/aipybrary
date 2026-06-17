import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router";
import { deleteMember, getMembers } from "../api/members";
import { apiErrorToFormMessage } from "../api/errors";
import type { Member } from "../api/types";
import { useCurrentUser } from "../auth/useCurrentUser";
import { canDeleteMembers, canManageMembers } from "../auth/roles";
import { MemberStatusBadge } from "./MemberStatusBadge";

interface MemberRowProps {
  member: Member;
  canManage: boolean;
  canDelete: boolean;
}

function MemberRow({ member, canManage, canDelete }: MemberRowProps) {
  const queryClient = useQueryClient();
  const [confirming, setConfirming] = useState(false);

  const remove = useMutation({
    mutationFn: () => deleteMember(member.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["members"] }),
  });

  return (
    <li className="rounded-lg bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to={`/members/${member.id}`} className="font-medium text-slate-900 hover:underline">
            {member.full_name}
          </Link>
          <p className="text-sm text-slate-600">{member.email}</p>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <MemberStatusBadge status={member.status} />
          {canManage && (
            <Link
              to={`/members/${member.id}/edit`}
              className="rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Edit
            </Link>
          )}
          {canDelete &&
            (confirming ? (
              <>
                <button
                  type="button"
                  onClick={() => remove.mutate()}
                  disabled={remove.isPending}
                  className="rounded-md bg-red-600 px-2.5 py-1 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
                >
                  {remove.isPending ? "Deleting…" : "Confirm"}
                </button>
                <button
                  type="button"
                  onClick={() => setConfirming(false)}
                  disabled={remove.isPending}
                  className="rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={() => setConfirming(true)}
                className="rounded-md border border-red-300 px-2.5 py-1 text-sm font-medium text-red-700 hover:bg-red-50"
              >
                Delete
              </button>
            ))}
        </div>
      </div>

      {remove.isError && (
        <p role="alert" className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700">
          {apiErrorToFormMessage(remove.error, "Failed to delete the member.")}
        </p>
      )}
    </li>
  );
}

export function MembersList() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ["members"],
    queryFn: getMembers,
  });
  const currentUser = useCurrentUser();
  const canManage = canManageMembers(currentUser.data?.role);
  const canDelete = canDeleteMembers(currentUser.data?.role);

  return (
    <section>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-slate-800">Members</h1>
        {canManage && (
          <Link
            to="/members/new"
            className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
          >
            New member
          </Link>
        )}
      </div>

      {isPending && <p className="text-slate-500">Loading members…</p>}

      {isError && (
        <p role="alert" className="rounded-md bg-red-50 p-4 text-red-700">
          {apiErrorToFormMessage(error, "Failed to load members.")}
        </p>
      )}

      {data &&
        (data.items.length === 0 ? (
          <p className="text-slate-500">No members found.</p>
        ) : (
          <ul className="space-y-3">
            {data.items.map((member) => (
              <MemberRow
                key={member.id}
                member={member}
                canManage={canManage}
                canDelete={canDelete}
              />
            ))}
          </ul>
        ))}
    </section>
  );
}
