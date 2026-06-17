import { describe, it, expect } from "vitest";
import { ApiError } from "./client";
import { apiErrorToFormMessage } from "./errors";

describe("apiErrorToFormMessage", () => {
  it("surfaces the backend detail carried by an ApiError (409/422)", () => {
    expect(apiErrorToFormMessage(new ApiError(409, "ISBN already exists"))).toBe(
      "ISBN already exists",
    );
    expect(apiErrorToFormMessage(new ApiError(422, "title is required"))).toBe("title is required");
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
