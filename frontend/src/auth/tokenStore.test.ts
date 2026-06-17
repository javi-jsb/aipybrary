import { describe, it, expect } from "vitest";
import { clearToken, getToken, setToken } from "./tokenStore";

describe("tokenStore", () => {
  it("returns null when no token is stored", () => {
    expect(getToken()).toBeNull();
  });

  it("persists a token and reads it back", () => {
    setToken("abc123");
    expect(getToken()).toBe("abc123");
  });

  it("overwrites a previously stored token", () => {
    setToken("first");
    setToken("second");
    expect(getToken()).toBe("second");
  });

  it("clears a stored token", () => {
    setToken("abc123");
    clearToken();
    expect(getToken()).toBeNull();
  });
});
