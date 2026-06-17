import { useQuery } from "@tanstack/react-query";
import { getCurrentUser } from "../api/users";
import { useAuth } from "./AuthContext";

/**
 * Resolves the authenticated user (`GET /auth/me`), cached by TanStack Query.
 * The query only runs while a session is held, so an unauthenticated render
 * never issues the request. Consumers read `data.role` to gate actions in the
 * UI — a usability aid only, not an authorization boundary (the server is the
 * authority).
 */
export function useCurrentUser() {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
    enabled: isAuthenticated,
  });
}
