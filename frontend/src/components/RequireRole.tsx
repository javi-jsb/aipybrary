import { Outlet } from "react-router";
import type { UserRole } from "../api/types";
import { useCurrentUser } from "../auth/useCurrentUser";
import { ForbiddenScreen } from "./ForbiddenScreen";

interface RequireRoleProps {
  /** Predicate from `roles.ts` deciding whether the resolved role may enter. */
  allow: (role: UserRole | undefined) => boolean;
}

/**
 * Layout-route guard: renders the nested routes (`<Outlet/>`) only when the
 * authenticated user's role passes `allow`, otherwise the {@link ForbiddenScreen}.
 * This mirrors the backend matrix for deep links the nav hides — the server
 * still enforces the boundary. While the role is still resolving (`GET /auth/me`
 * in flight) it renders nothing, avoiding a "not allowed" flash before the role
 * is known.
 */
export function RequireRole({ allow }: RequireRoleProps) {
  const currentUser = useCurrentUser();

  if (currentUser.isPending) {
    return null;
  }
  if (!allow(currentUser.data?.role)) {
    return <ForbiddenScreen />;
  }
  return <Outlet />;
}
