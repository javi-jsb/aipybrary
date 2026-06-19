import { useEffect, useState, type ReactNode } from "react";
import { login as loginRequest } from "../api/auth";
import { setUnauthorizedHandler } from "../api/client";
import { AuthContext } from "./AuthContext";
import { clearToken, getToken, setToken } from "./tokenStore";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(() => getToken() !== null);

  async function login(username: string, password: string) {
    // The token is only stored on success; a failed request throws before this
    // line, leaving the unauthenticated state untouched.
    const { access_token } = await loginRequest({ username, password });
    setToken(access_token);
    setIsAuthenticated(true);
  }

  function logout() {
    clearToken();
    setIsAuthenticated(false);
  }

  // A `401` from any request means the session is gone (expired/invalid token):
  // drop it so `ProtectedLayout` redirects to login. Distinct from `403`, which
  // is handled per-view as a "not allowed" message.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearToken();
      setIsAuthenticated(false);
    });
    return () => setUnauthorizedHandler(null);
  }, []);

  return <AuthContext value={{ isAuthenticated, login, logout }}>{children}</AuthContext>;
}
