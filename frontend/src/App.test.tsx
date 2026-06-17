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

describe("App routing and auth gating", () => {
  it("redirects to the login screen when no token is stored", () => {
    renderWithAuth(<App />);

    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    // The protected view must not mount, so no books request is issued.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("redirects a protected deep link to login when unauthenticated", () => {
    renderWithAuth(<App />, { initialEntries: ["/books"] });

    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders the books view at /books when a token is present", async () => {
    setToken("tok");
    fetchMock.mockResolvedValue(jsonResponse({ items: [], total: 0, page: 1, size: 50, pages: 0 }));
    renderWithAuth(<App />, { initialEntries: ["/books"] });

    expect(await screen.findByRole("heading", { name: "Books" })).toBeInTheDocument();
  });
});
