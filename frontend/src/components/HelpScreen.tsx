import type { UserRole } from "../api/types";
import {
  canDeleteMembers,
  canManageBooks,
  canManageCopies,
  canManageLoans,
  canManageMembers,
  canViewMembers,
} from "../auth/roles";

/** The roles, in capability order (narrowest first), used as the matrix columns. */
const ROLES: readonly UserRole[] = ["member", "staff", "admin"];

interface Capability {
  /** Human label for the matrix row. */
  label: string;
  /**
   * Whether the given role may perform it. Read capabilities are open to every
   * authenticated user (`() => true`); managed ones defer to the real helpers in
   * `roles.ts` so a cell can never drift from the actual UI gating.
   */
  allows: (role: UserRole) => boolean;
}

/**
 * The capability matrix, grouped per feature. The managed rows call the same
 * `roles.ts` predicates the screens use, so the ✓/— here always matches what a
 * given role actually sees. Adding a feature or changing a permission means
 * adding/adjusting a row here (see the maintenance rule in `CLAUDE.md`).
 */
const FEATURES: readonly { feature: string; capabilities: readonly Capability[] }[] = [
  {
    feature: "Books",
    capabilities: [
      { label: "View the catalog", allows: () => true },
      { label: "Create, edit, delete books", allows: canManageBooks },
    ],
  },
  {
    feature: "Book copies",
    capabilities: [
      { label: "View a book's copies", allows: () => true },
      { label: "Add, remove copies", allows: canManageCopies },
    ],
  },
  {
    feature: "Members",
    capabilities: [
      { label: "View the members list", allows: canViewMembers },
      { label: "Create, edit members", allows: canManageMembers },
      { label: "Delete members", allows: canDeleteMembers },
    ],
  },
  {
    feature: "Loans",
    capabilities: [
      { label: "View loans", allows: () => true },
      { label: "Borrow, return loans", allows: canManageLoans },
    ],
  },
];

/** A short prose description of each feature, shown above the matrix. */
const FEATURE_NOTES: readonly { title: string; body: string }[] = [
  {
    title: "Books",
    body: "Full catalogue CRUD. Each book carries a title, author, and optional ISBN, publication year, and synopsis. The ISBN-10/13 checksum and the year are validated client-side before saving.",
  },
  {
    title: "Book copies",
    body: "The physical copies of a book, each with a unique barcode and optional location and notes. A book's availability is derived from how many of its copies are not currently on loan.",
  },
  {
    title: "Members",
    body: "Library members. Creating one provisions a linked member-role user and returns a one-time initial password (shown only once). A member cannot be deleted while they still have loans — the backend rejects it with a 409. The members list is staff-only: a signed-in member has no members navigation and may only read their own record.",
  },
  {
    title: "Loans",
    body: "Borrowing and returning. A loan links a member to a specific book copy; the due date is assigned by the server. Its status (active, overdue, returned) is computed from the due date and return time. Members view loans read-only and see only their own; staff borrow and return on their behalf.",
  },
];

/** Render one capability cell: a check when allowed, a dash otherwise. */
function Cell({ allowed }: { allowed: boolean }) {
  return (
    <td className="px-3 py-2 text-center">
      {allowed ? (
        <span className="text-emerald-600" aria-label="allowed">
          ✓
        </span>
      ) : (
        <span className="text-slate-300" aria-label="not allowed">
          —
        </span>
      )}
    </td>
  );
}

/**
 * Help view (`/help`): a concise overview of what the app does and the role
 * capability matrix. Any authenticated user may open it. The matrix is derived
 * from the `roles.ts` predicates, so it stays accurate to the actual UI gating.
 */
export function HelpScreen() {
  return (
    <section className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-slate-800">Help</h1>
        <p className="mt-2 text-sm text-slate-600">
          aipybrary manages a book library: its catalogue and physical copies, the members who
          borrow them, and the loans between the two. Below is what each feature does and who can do
          what.
        </p>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-800">Features</h2>
        <dl className="space-y-3">
          {FEATURE_NOTES.map((note) => (
            <div key={note.title} className="rounded-lg bg-white p-4 shadow-sm">
              <dt className="font-medium text-slate-900">{note.title}</dt>
              <dd className="mt-1 text-sm text-slate-600">{note.body}</dd>
            </div>
          ))}
        </dl>
      </div>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-800">Role capabilities</h2>
        <div className="overflow-x-auto rounded-lg bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="px-3 py-2 text-left font-medium">Capability</th>
                {ROLES.map((role) => (
                  <th key={role} className="px-3 py-2 text-center font-medium capitalize">
                    {role}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FEATURES.map((group) => (
                <FeatureRows key={group.feature} feature={group.feature} group={group} />
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-500">
          The backend <strong>enforces</strong> these permissions server-side — it is the security
          boundary. This interface mirrors the same matrix to hide controls, navigation, and pages a
          role may not use; reaching a forbidden action directly still returns a "not allowed"
          response.
        </p>
      </div>
    </section>
  );
}

/** The rows for one feature: a group header followed by its capability rows. */
function FeatureRows({
  feature,
  group,
}: {
  feature: string;
  group: { capabilities: readonly Capability[] };
}) {
  return (
    <>
      <tr className="border-b border-slate-100 bg-slate-50">
        <th
          colSpan={ROLES.length + 1}
          className="px-3 py-1.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
        >
          {feature}
        </th>
      </tr>
      {group.capabilities.map((capability) => (
        <tr key={capability.label} className="border-b border-slate-100 last:border-0">
          <td className="px-3 py-2 text-slate-700">{capability.label}</td>
          {ROLES.map((role) => (
            <Cell key={role} allowed={capability.allows(role)} />
          ))}
        </tr>
      ))}
    </>
  );
}
