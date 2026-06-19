import { Link } from "react-router";
import { DEFAULT_AUTHENTICATED_ROUTE } from "../routes";

/**
 * Shown when an authenticated user reaches a route their role may not use (a
 * deep link the nav doesn't surface) — the frontend's graceful `403` handling.
 * The backend is the real boundary; this just turns a forbidden destination into
 * a clear "not allowed" message instead of a blank or raw-error state. Distinct
 * from the `401`/session-expired path, which redirects to login.
 */
export function ForbiddenScreen() {
  return (
    <section className="mx-auto max-w-md text-center">
      <h1 className="text-xl font-semibold text-slate-800">Not allowed</h1>
      <p className="mt-2 text-sm text-slate-600">
        Your role doesn&rsquo;t have access to this page.
      </p>
      <Link
        to={DEFAULT_AUTHENTICATED_ROUTE}
        className="mt-4 inline-block rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700"
      >
        Back to books
      </Link>
    </section>
  );
}
