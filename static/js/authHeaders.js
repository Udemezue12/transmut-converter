import { getCSRFToken } from "./csrf.js";
import { getCookie } from "./cookies.js";
export async function getAuthHeaders() {
  const csrf = await getCSRFToken();
  const token = getCookie("access_token");

  const headers = {};
  if (csrf) headers["X-CSRF-Token"] = csrf;
  if (token) headers["Authorization"] = "Bearer " + token;

  return headers;
}
