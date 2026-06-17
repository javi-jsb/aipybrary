import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { LoginScreen } from "./LoginScreen";
import { getToken, setToken } from "../auth/tokenStore";
import { jsonResponse, renderWithAuth } from "../test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

beforeEach(() => {
  fetchMock.mockReset();
});

describe("LoginScreen", () => {
  it("renders the credentials form", () => {
    renderWithAuth(<LoginScreen />);

    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("submits url-encoded credentials and stores the returned token", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ access_token: "jwt-xyz", token_type: "bearer" }));
    const user = userEvent.setup();
    renderWithAuth(<LoginScreen />);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "secret");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/auth/login");
    const init = fetchMock.mock.calls[0][1]!;
    expect((init.headers as Headers).get("Content-Type")).toBe("application/x-www-form-urlencoded");
    expect((init.body as URLSearchParams).toString()).toBe(
      "username=user%40example.com&password=secret",
    );
    await waitFor(() => expect(getToken()).toBe("jwt-xyz"));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("surfaces the backend error message when login fails", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Invalid credentials" }, 401));
    const user = userEvent.setup();
    renderWithAuth(<LoginScreen />);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Sign in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid credentials");
    expect(getToken()).toBeNull();
  });

  it("redirects away from the login route when already authenticated", () => {
    setToken("tok");
    renderWithAuth(
      <Routes>
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/books" element={<div>Books route</div>} />
      </Routes>,
      { initialEntries: ["/login"] },
    );

    expect(screen.getByText("Books route")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Sign in" })).not.toBeInTheDocument();
  });
});
