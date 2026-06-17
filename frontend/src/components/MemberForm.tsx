import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router";
import { createMember, getMember, updateMember } from "../api/members";
import { apiErrorToFormMessage } from "../api/errors";
import type { Member, MemberCreateResponse, MemberStatus } from "../api/types";
import {
  EMPTY_MEMBER_FORM_VALUES,
  validateMemberForm,
  type MemberFieldErrors,
  type MemberFormValues,
} from "./memberValidation";

function toFormValues(member: Member): MemberFormValues {
  return {
    fullName: member.full_name,
    email: member.email,
    status: member.status,
  };
}

const STATUSES: readonly MemberStatus[] = ["active", "suspended"];

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

/** Shown once after a successful create: the one-time `initial_password` the
 * backend generated. It is never available again on subsequent reads, so the
 * panel makes clear it must be copied now. */
function CreatedPanel({ member }: { member: MemberCreateResponse }) {
  return (
    <section>
      <h1 className="mb-6 text-xl font-semibold text-slate-800">Member created</h1>

      <div className="max-w-lg space-y-4 rounded-lg bg-white p-4 shadow-sm">
        <p className="text-slate-700">
          <span className="font-medium">{member.full_name}</span> ({member.email}) was created.
        </p>
        <div>
          <p className="text-sm font-medium text-slate-700">Initial password</p>
          <p className="mt-1 rounded-md bg-slate-100 px-3 py-2 font-mono text-slate-900">
            {member.initial_password}
          </p>
          <p className="mt-1 text-xs text-amber-700">
            Copy this now — it is shown only once and cannot be retrieved later.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to={`/members/${member.id}`}
            className="rounded-md bg-slate-800 px-4 py-2 font-medium text-white hover:bg-slate-700"
          >
            View member
          </Link>
          <Link to="/members" className="text-sm font-medium text-slate-600 hover:text-slate-800">
            Back to members
          </Link>
        </div>
      </div>
    </section>
  );
}

interface FieldsProps {
  /** Present in edit mode; drives PATCH vs POST. */
  memberId?: string;
  initial: MemberFormValues;
}

function MemberFormFields({ memberId, initial }: FieldsProps) {
  const isEdit = memberId !== undefined;
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [values, setValues] = useState<MemberFormValues>(initial);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<MemberFieldErrors>({});
  const [created, setCreated] = useState<MemberCreateResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () => {
      const fullName = values.fullName.trim();
      if (isEdit) {
        return updateMember(memberId, { full_name: fullName, status: values.status });
      }
      return createMember({
        full_name: fullName,
        email: values.email.trim().toLowerCase(),
        status: values.status,
      });
    },
    onSuccess: (result) => {
      // Refresh the list (and this member's detail) so the change shows on return.
      queryClient.invalidateQueries({ queryKey: ["members"] });
      if (isEdit) {
        queryClient.invalidateQueries({ queryKey: ["member", memberId] });
        navigate(`/members/${memberId}`);
      } else {
        // Hold the create response so the one-time initial password can be shown.
        setCreated(result as MemberCreateResponse);
      }
    },
    onError: (err) => setError(apiErrorToFormMessage(err)),
  });

  if (created) {
    return <CreatedPanel member={created} />;
  }

  function update<K extends keyof MemberFormValues>(key: K, value: MemberFormValues[K]) {
    setValues((prev) => ({ ...prev, [key]: value }));
    // Clear a field's error as the user edits it, so stale messages don't linger.
    setFieldErrors((prev) => (prev[key] ? { ...prev, [key]: undefined } : prev));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    // Validate client-side first so invalid input never costs a 422 round-trip.
    const errors = validateMemberForm(values, { isEdit });
    if (Object.values(errors).some(Boolean)) {
      setFieldErrors(errors);
      return;
    }
    setFieldErrors({});
    mutation.mutate();
  }

  return (
    <section>
      <h1 className="mb-6 text-xl font-semibold text-slate-800">
        {isEdit ? "Edit member" : "New member"}
      </h1>

      <form onSubmit={handleSubmit} noValidate className="max-w-lg space-y-4">
        <div className="space-y-1">
          <label htmlFor="fullName" className="block text-sm font-medium text-slate-700">
            Full name
          </label>
          <input
            id="fullName"
            value={values.fullName}
            onChange={(e) => update("fullName", e.target.value)}
            aria-invalid={fieldErrors.fullName !== undefined}
            aria-describedby={fieldErrors.fullName ? "fullName-error" : undefined}
            className={fieldClass(fieldErrors.fullName)}
          />
          <FieldError id="fullName-error" message={fieldErrors.fullName} />
        </div>

        <div className="space-y-1">
          <label htmlFor="email" className="block text-sm font-medium text-slate-700">
            Email
          </label>
          {isEdit ? (
            // Email is owned by the linked user and not editable here.
            <p id="email" className="text-slate-600">
              {values.email}
            </p>
          ) : (
            <input
              id="email"
              type="email"
              value={values.email}
              onChange={(e) => update("email", e.target.value)}
              aria-invalid={fieldErrors.email !== undefined}
              aria-describedby={fieldErrors.email ? "email-error" : undefined}
              className={fieldClass(fieldErrors.email)}
            />
          )}
          <FieldError id="email-error" message={fieldErrors.email} />
        </div>

        <div className="space-y-1">
          <label htmlFor="status" className="block text-sm font-medium text-slate-700">
            Status
          </label>
          <select
            id="status"
            value={values.status}
            onChange={(e) => update("status", e.target.value as MemberStatus)}
            className={inputClass}
          >
            {STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
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
          <Link
            to={isEdit ? `/members/${memberId}` : "/members"}
            className="text-sm font-medium text-slate-600 hover:text-slate-800"
          >
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}

/**
 * Member create/edit form. In edit mode (`/members/:id/edit`) it fetches the
 * member to prefill the fields (email read-only, since it is owned by the linked
 * user); in create mode (`/members/new`) it starts blank and, on success, shows
 * the one-time `initial_password` returned by the API. Both submit through
 * `useMutation` over `apiClient` and surface `409`/`422` errors on the form.
 */
export function MemberForm() {
  const { id } = useParams<{ id: string }>();

  const member = useQuery({
    queryKey: ["member", id],
    queryFn: () => getMember(id!),
    enabled: id !== undefined,
  });

  if (id === undefined) {
    return <MemberFormFields initial={EMPTY_MEMBER_FORM_VALUES} />;
  }

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

  // Remount when the loaded member changes so the controlled fields re-seed.
  return (
    <MemberFormFields
      key={member.data.id}
      memberId={member.data.id}
      initial={toFormValues(member.data)}
    />
  );
}
