import { getAuthHeaders } from "./authHeaders.js";
export async function refreshAccessToken() {
  try {
    const resp = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      credentials: "include",
      headers: await getAuthHeaders(),
    });

    if (resp.status === 401) {
      showToast("Session expired. Please log in again.", "error");
      setTimeout(() => {
        window.location.href = window.APP_CONFIG.loginUrl;
      }, 1500);
      return false;
    }

    if (!resp.ok) return false;

    return true;
  } catch {
    return false;
  }
}