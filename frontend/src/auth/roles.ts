import type { UserRole } from "../api/types";

/** Roles allowed to manage the catalog (create/edit/delete books). */
const BOOK_MANAGER_ROLES: readonly UserRole[] = ["admin", "staff"];

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
