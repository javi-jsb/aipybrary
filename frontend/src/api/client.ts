import { getToken } from "../auth/tokenStore";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8077";

/** Raised when the backend responds with a non-success status code. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: BodyInit;
  headers?: Record<string, string>;
}

type UnauthorizedHandler = () => void;

let unauthorizedHandler: UnauthorizedHandler | null = null;

/**
 * Register a callback invoked whenever a request comes back `401 Unauthorized`
 * (a missing/invalid/expired token — a session problem). `AuthProvider` wires
 * this to `logout` so an expired token drops the session and redirects to login,
 * keeping that path distinct from the `403`/"not allowed" handling. The error is
 * still thrown afterwards, so call sites can surface their own message.
 */
export function setUnauthorizedHandler(handler: UnauthorizedHandler | null): void {
  unauthorizedHandler = handler;
}

/**
 * Single seam for all backend requests: prepends the configured base URL,
 * attaches the stored access token as a bearer header when present, parses
 * JSON responses, and surfaces non-success responses as {@link ApiError}.
 */
export async function apiClient<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body,
  });

  if (!response.ok) {
    if (response.status === 401) {
      // A session problem (expired/invalid token) — let the app drop the
      // session and redirect to login, distinct from a 403 "not allowed".
      unauthorizedHandler?.();
    }
    throw new ApiError(response.status, await extractErrorMessage(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json();
    if (data && typeof data === "object" && "detail" in data && typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // Body was empty or not JSON — fall back to a generic message.
  }
  return `Request failed with status ${response.status}`;
}
