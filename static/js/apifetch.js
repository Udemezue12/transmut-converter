import { getAuthHeaders } from "./authHeaders.js";
import { refreshAccessToken } from "./refreshAcessTokens.js";
export async function apiFetch(url, options = {}) {
  options.credentials = "include";

  const authHeaders = await getAuthHeaders();
  options.headers = { ...authHeaders, ...(options.headers || {}) };

  let resp = await fetch(url, options);

  if (resp.status === 401) {
    const refreshed = await refreshAccessToken();
    if (!refreshed) return resp;

    const newHeaders = await getAuthHeaders();
    options.headers = { ...newHeaders, ...(options.headers || {}) };

    resp = await fetch(url, options);
  }

  return resp;
}
