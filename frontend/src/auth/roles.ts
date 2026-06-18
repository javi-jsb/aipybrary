import type { UserRole } from "../api/types";

/** Roles allowed to manage the catalog (create/edit/delete books). */
const BOOK_MANAGER_ROLES: readonly UserRole[] = ["admin", "staff"];

/** Roles allowed to manage members (create/edit). Pinned per entity slice so
 * the matrix can diverge from books without coupling the two. */
const MEMBER_MANAGER_ROLES: readonly UserRole[] = ["admin", "staff"];

/** Roles allowed to delete members. Narrower than create/edit: deletion is
 * destructive (and the backend rejects it for members with loans), so only
 * admins may do it. */
const MEMBER_DELETER_ROLES: readonly UserRole[] = ["admin"];

/** Roles allowed to add/remove a book's copies. Pinned per entity slice, like
 * the books matrix it currently mirrors. */
const COPY_MANAGER_ROLES: readonly UserRole[] = ["admin", "staff"];

/** Roles allowed to borrow and return loans. Pinned per entity slice; mirrors
 * the staff-facing catalog roles (a `member` views loans read-only). */
const LOAN_MANAGER_ROLES: readonly UserRole[] = ["admin", "staff"];

/**
 * Whether the given role may see the book create/edit/delete controls.
 *
 * UX-only: the backend does not currently enforce role authorization, so this
 * merely hides controls — it is not a security boundary. An undefined role
 * (current user not yet resolved) is treated as not allowed.
 */
export function canManageBooks(role: UserRole | undefined): boolean {
  return role !== undefined && BOOK_MANAGER_ROLES.includes(role);
}

/**
 * Whether the given role may see the member create/edit controls. Same UX-only
 * caveat as {@link canManageBooks}: it hides controls, it is not a security
 * boundary.
 */
export function canManageMembers(role: UserRole | undefined): boolean {
  return role !== undefined && MEMBER_MANAGER_ROLES.includes(role);
}

/**
 * Whether the given role may see the member delete control. Same UX-only caveat
 * as {@link canManageBooks}: it hides the control, it is not a security
 * boundary.
 */
export function canDeleteMembers(role: UserRole | undefined): boolean {
  return role !== undefined && MEMBER_DELETER_ROLES.includes(role);
}

/**
 * Whether the given role may see the add/remove-copy controls. Same UX-only
 * caveat as {@link canManageBooks}: it hides controls, it is not a security
 * boundary.
 */
export function canManageCopies(role: UserRole | undefined): boolean {
  return role !== undefined && COPY_MANAGER_ROLES.includes(role);
}

/**
 * Whether the given role may see the borrow/return controls. Same UX-only caveat
 * as {@link canManageBooks}: it hides controls, it is not a security boundary.
 */
export function canManageLoans(role: UserRole | undefined): boolean {
  return role !== undefined && LOAN_MANAGER_ROLES.includes(role);
}
