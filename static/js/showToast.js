export function showToast(msg, type = "info") {
  const c = document.getElementById("toastContainer"),
    t = document.createElement("div");
  t.className = "toast " + type;
  t.innerHTML = '<div class="toast-dot"></div><span>' + msg + "</span>";
  c.appendChild(t);
  setTimeout(() => {
    t.style.opacity = "0";
    t.style.transition = "opacity 0.3s";
    setTimeout(() => t.remove(), 300);
  }, 3500);
}
