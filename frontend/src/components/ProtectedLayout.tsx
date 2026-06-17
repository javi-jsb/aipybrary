import { useQueryClient } from "@tanstack/react-query";
import { NavLink, Navigate, Outlet } from "react-router";
import { useAuth } from "../auth/AuthContext";
import { useCurrentUser } from "../auth/useCurrentUser";
import { LOGIN_ROUTE } from "../routes";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium ${
    isActive ? "bg-slate-800 text-white" : "text-slate-700 hover:bg-slate-100"
  }`;

/**
 * Authenticated shell: persistent nav + sign-out wrapping the routed view via
 * `<Outlet/>`. Unauthenticated access is redirected to the login route, so the
 * protected views (and their requests) never mount without a session.
 */
export function ProtectedLayout() {
  const { isAuthenticated, logout } = useAuth();
  const queryClient = useQueryClient();
  const currentUser = useCurrentUser();

  if (!isAuthenticated) {
    return <Navigate to={LOGIN_ROUTE} replace />;
  }

  function handleSignOut() {
    logout();
    // Drop cached server state so a different user's data never leaks into the
    // next session that reuses this client.
    queryClient.clear();
  }

  return (
    <div className="min-h-screen bg-slate-100">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-center gap-6">
          <span className="text-lg font-semibold text-slate-800">aipybrary</span>
          <nav className="flex items-center gap-2">
            <NavLink to="/books" className={navLinkClass}>
              Books
            </NavLink>
            <NavLink to="/members" className={navLinkClass}>
              Members
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {currentUser.data && (
            <span className="text-sm text-slate-500">
              {currentUser.data.email}
              <span className="ml-2 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                {currentUser.data.role}
              </span>
            </span>
          )}
          <button
            type="button"
            onClick={handleSignOut}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-3xl p-6">
        <Outlet />
      </main>
    </div>
  );
}
