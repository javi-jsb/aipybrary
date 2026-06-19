import { describe, it, expect } from "vitest";
import { ApiError } from "./client";
import {
  apiErrorToFormMessage,
  FORBIDDEN_MESSAGE,
  isForbiddenError,
  isUnauthorizedError,
} from "./errors";

describe("apiErrorToFormMessage", () => {
  it("surfaces the backend detail carried by an ApiError (409/422)", () => {
    expect(apiErrorToFormMessage(new ApiError(409, "ISBN already exists"))).toBe(
      "ISBN already exists",
    );
    expect(apiErrorToFormMessage(new ApiError(422, "title is required"))).toBe("title is required");
  });

  it("returns the friendly forbidden message for a 403, not the raw detail", () => {
    expect(apiErrorToFormMessage(new ApiError(403, "Insufficient permissions"))).toBe(
      FORBIDDEN_MESSAGE,
    );
  });

  it("collapses non-ApiError throws to the generic fallback", () => {
    expect(apiErrorToFormMessage(new Error("connection reset"))).toBe(
      "Something went wrong. Please try again.",
    );
    expect(apiErrorToFormMessage("boom")).toBe("Something went wrong. Please try again.");
  });

  it("uses a caller-provided fallback for non-ApiError throws", () => {
    expect(apiErrorToFormMessage(undefined, "Login failed. Please try again.")).toBe(
      "Login failed. Please try again.",
    );
  });
});

describe("isForbiddenError / isUnauthorizedError", () => {
  it("recognises a 403 as forbidden and nothing else", () => {
    expect(isForbiddenError(new ApiError(403, "nope"))).toBe(true);
    expect(isForbiddenError(new ApiError(401, "nope"))).toBe(false);
    expect(isForbiddenError(new Error("boom"))).toBe(false);
    expect(isForbiddenError("boom")).toBe(false);
  });

  it("recognises a 401 as unauthorized and nothing else", () => {
    expect(isUnauthorizedError(new ApiError(401, "nope"))).toBe(true);
    expect(isUnauthorizedError(new ApiError(403, "nope"))).toBe(false);
    expect(isUnauthorizedError(new Error("boom"))).toBe(false);
  });
});
