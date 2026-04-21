export async function getCSRFToken() {
  try {
    const res = await fetch("/api/v1/csrf_token", {
      method: "GET",
    //   credentials: "include", // keep this if you're using cookies/session
    });

    if (!res.ok) {
      throw new Error("Failed to get CSRF token");
    }

    const data = await res.json();
    return data.csrf_token || "";
  } catch (err) {
    console.error("Error fetching CSRF token:", err);
    return "";
  }
}