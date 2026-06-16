import { useState, type ReactNode } from "react";
import { login as loginRequest } from "../api/auth";
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

  return <AuthContext value={{ isAuthenticated, login, logout }}>{children}</AuthContext>;
}
