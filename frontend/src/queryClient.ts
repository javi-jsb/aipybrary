import { QueryClient } from "@tanstack/react-query";

/**
 * Single application-wide query client. Server state (lists, details, the
 * current user) lives here; mutations invalidate the affected keys so views
 * refresh automatically. Kept in its own module so both the app entry point
 * and tests can construct/replace it without importing the React tree.
 */
export const queryClient = new QueryClient();
