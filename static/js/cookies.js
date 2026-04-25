export function getCookie(n) {
  const m = document.cookie.match(
    new RegExp(
      "(?:^|; )" + n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)",
    ),
  );
  return m ? decodeURIComponent(m[1]) : null;
}

export function hasAccessToken() {
  return !!getCookie("access_token");
}