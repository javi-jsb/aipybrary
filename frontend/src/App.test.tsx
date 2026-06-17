import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import App from "./App";
import { setToken } from "./auth/tokenStore";
import { jsonResponse, renderWithAuth } from "./test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

beforeEach(() => {
  fetchMock.mockReset();
});

describe("App auth gating", () => {
  it("renders the login screen when no token is stored", () => {
    renderWithAuth(<App />);

    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    // The protected view must not mount, so no books request is issued.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders the books view when a token is present", async () => {
    setToken("tok");
    fetchMock.mockResolvedValue(jsonResponse({ items: [], total: 0, page: 1, size: 50, pages: 0 }));
    renderWithAuth(<App />);

    expect(await screen.findByRole("heading", { name: "Books" })).toBeInTheDocument();
  });
});
