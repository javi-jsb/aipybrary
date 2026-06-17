import { describe, it, expect } from "vitest";
import {
  EMPTY_MEMBER_FORM_VALUES,
  validateEmail,
  validateMemberForm,
  type MemberFormValues,
} from "./memberValidation";

describe("validateEmail", () => {
  it("accepts a well-formed email", () => {
    expect(validateEmail("ada@example.com")).toBeNull();
  });

  it("normalizes before validating (trim + lowercase)", () => {
    expect(validateEmail("  Ada@Example.com  ")).toBeNull();
  });

  it.each([["missing-at"], ["no@domain"], ["@example.com"], ["spaced @example.com"]])(
    "rejects malformed email %s",
    (value) => {
      expect(validateEmail(value)).toBe("Invalid email format.");
    },
  );

  it("rejects an empty email as required", () => {
    expect(validateEmail("   ")).toBe("Email is required.");
  });
});

function values(overrides: Partial<MemberFormValues> = {}): MemberFormValues {
  return { ...EMPTY_MEMBER_FORM_VALUES, fullName: "Ada", email: "ada@example.com", ...overrides };
}

describe("validateMemberForm", () => {
  it("returns no errors for valid create values", () => {
    expect(validateMemberForm(values(), { isEdit: false })).toEqual({});
  });

  it("requires a full name", () => {
    expect(validateMemberForm(values({ fullName: "  " }), { isEdit: false })).toEqual({
      fullName: "Full name is required.",
    });
  });

  it("rejects a too-long full name", () => {
    const errors = validateMemberForm(values({ fullName: "a".repeat(301) }), { isEdit: false });
    expect(errors.fullName).toMatch(/at most 300/);
  });

  it("validates email on create", () => {
    expect(validateMemberForm(values({ email: "bad" }), { isEdit: false })).toEqual({
      email: "Invalid email format.",
    });
  });

  it("skips email validation on edit (email is not editable there)", () => {
    expect(validateMemberForm(values({ email: "" }), { isEdit: true })).toEqual({});
  });
});
