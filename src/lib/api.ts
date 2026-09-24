/**
 * apiFetch: base-path aware fetch wrapper.
 * - Endpoints starting with '/auth' or '/workspaces' are served under /api/ directly.
 * - Endpoints starting with '/v1/' already contain the version prefix; map to /api/v1/...
 * - All other endpoints are served under /api/v1/.
 * Never stores credentials in localStorage. Relies on HttpOnly session cookie set by the backend.
 */
export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // Auth and bare-workspace routes live at /api/; v1-prefixed routes at /api/v1/...
  const isAuthOrWorkspace = endpoint.startsWith("/auth") || endpoint.startsWith("/workspaces");
  const isV1Prefixed = endpoint.startsWith("/v1/");
  const url = isAuthOrWorkspace
    ? `/api${endpoint}`
    : isV1Prefixed
    ? `/api${endpoint}`
    : `/api/v1${endpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && options.method !== 'GET' && options.body) {
    headers.set('Content-Type', 'application/json');
  }
  
  // Ensure we don't receive cached responses for authenticated requests
  headers.set('Cache-Control', 'no-store');

  const config: RequestInit = {
    ...options,
    headers,
    credentials: 'same-origin', // always send session cookie, never localStorage tokens
    cache: 'no-store',
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}
