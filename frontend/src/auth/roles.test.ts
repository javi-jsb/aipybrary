import { describe, it, expect } from "vitest";
import type { UserRole } from "../api/types";
import {
  canDeleteMembers,
  canManageBooks,
  canManageCopies,
  canManageLoans,
  canManageMembers,
  canViewMembers,
} from "./roles";

/** The matrix each predicate must satisfy, by role. `undefined` models the role
 * not yet being resolved (the current-user query still in flight). */
const CASES: ReadonlyArray<{
  name: string;
  predicate: (role: UserRole | undefined) => boolean;
  admin: boolean;
  staff: boolean;
  member: boolean;
}> = [
  { name: "canManageBooks", predicate: canManageBooks, admin: true, staff: true, member: false },
  { name: "canManageCopies", predicate: canManageCopies, admin: true, staff: true, member: false },
  { name: "canViewMembers", predicate: canViewMembers, admin: true, staff: true, member: false },
  {
    name: "canManageMembers",
    predicate: canManageMembers,
    admin: true,
    staff: true,
    member: false,
  },
  {
    name: "canDeleteMembers",
    predicate: canDeleteMembers,
    admin: true,
    staff: false,
    member: false,
  },
  { name: "canManageLoans", predicate: canManageLoans, admin: true, staff: true, member: false },
];

describe("roles gating predicates", () => {
  for (const c of CASES) {
    it(`${c.name} mirrors the matrix per role`, () => {
      expect(c.predicate("admin")).toBe(c.admin);
      expect(c.predicate("staff")).toBe(c.staff);
      expect(c.predicate("member")).toBe(c.member);
    });

    it(`${c.name} denies an unresolved (undefined) role`, () => {
      expect(c.predicate(undefined)).toBe(false);
    });
  }
});
