// Single seam for access-token persistence. The storage mechanism is an
// implementation detail kept behind these functions so it can be hardened
// later (e.g. moved off localStorage) without touching call sites.
const STORAGE_KEY = "aipybrary.access_token";

export function getToken(): string | null {
  return localStorage.getItem(STORAGE_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(STORAGE_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(STORAGE_KEY);
}
