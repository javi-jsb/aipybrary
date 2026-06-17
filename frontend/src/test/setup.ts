// Global test setup, loaded via vitest's `setupFiles`.
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// With vitest globals disabled, React Testing Library's automatic cleanup is
// not registered, so unmount rendered trees ourselves. Also reset the token
// store (backed by localStorage) so tests stay isolated.
afterEach(() => {
  cleanup();
  localStorage.clear();
});
