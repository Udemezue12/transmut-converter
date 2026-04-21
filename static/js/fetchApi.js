import { getCSRFToken } from "./csrf.js";
function redirectIfUnauthed() {
  window.location.href = "/";
}
export async function apiFetch(url, options = {}, retry = true) {
  try {
    const res = await fetch(url, {
      credentials: "include",
      headers: {
        "X-CSRF-Token": await getCSRFToken(),
        ...(options.headers || {}),
      },
      ...options,
    });

    if (res.status === 401 && retry) {
      const refreshRes = await fetch("/api/v1/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: {
          "X-CSRF-Token": await getCSRFToken(),
        },
      });

      if (refreshRes.ok) {
        return apiFetch(url, options, false);
      }
    }

    if (res.status === 401 || res.status === 403) {
      redirectIfUnauthed();
      return null;
    }

    if (!res.ok) throw new Error("Request failed");

    return res;
  } catch (e) {
    showToast(e.message || "Network error", false);
    return null;
  }
}
