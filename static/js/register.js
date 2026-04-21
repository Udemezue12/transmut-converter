import { getCSRFToken } from "./csrf.js";

const pwInput = document.getElementById("reg-password");
const cfInput = document.getElementById("reg-confirm");
const bar = document.getElementById("strength-bar");
const lbl = document.getElementById("strength-label");
const matchEl = document.getElementById("confirm-match");


pwInput.addEventListener("input", function () {
  const val = this.value;
  if (!val) {
    bar.style.width = "0";
    lbl.textContent = "";
    return;
  }

  let s = 0;
  if (val.length >= 8) s++;
  if (/[A-Z]/.test(val)) s++;
  if (/[0-9]/.test(val)) s++;
  if (/[^A-Za-z0-9]/.test(val)) s++;

  const cfg = [
    { color: "#c94a2a", text: "Weak", w: "25%" },
    { color: "#c47e1a", text: "Fair", w: "50%" },
    { color: "#4a6fa5", text: "Good", w: "75%" },
    { color: "#3d7a5e", text: "Strong", w: "100%" },
  ];
  const c = cfg[Math.max(0, s - 1)];
  bar.style.background = c.color;
  bar.style.width = c.w;
  lbl.textContent = c.text;
  lbl.style.color = c.color;

  checkConfirm();
});


function checkConfirm() {
  if (!cfInput.value) return;
  matchEl.style.display = "block";
  if (cfInput.value === pwInput.value) {
    matchEl.textContent = "✓ Passwords match";
    matchEl.style.color = "#3d7a5e";
    cfInput.classList.remove("error");
    cfInput.classList.add("valid");
  } else {
    matchEl.textContent = "✕ Passwords do not match";
    matchEl.style.color = "#c94a2a";
    cfInput.classList.add("error");
    cfInput.classList.remove("valid");
  }
}
cfInput.addEventListener("input", checkConfirm);


document.querySelectorAll("input").forEach((inp) => {
  inp.addEventListener("focus", () => {
    inp
      .closest(".field")
      ?.querySelector("label")
      ?.style.setProperty("color", "var(--ink-2)");
  });
  inp.addEventListener("blur", () => {
    inp
      .closest(".field")
      ?.querySelector("label")
      ?.style.setProperty("color", "var(--ink-4)");
  });
});


document
  .getElementById("register-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    if (cfInput.value !== pwInput.value) {
      checkConfirm();
      cfInput.focus();
      return;
    }

    const btn = document.getElementById("register-btn");
    const btnText = document.getElementById("register-btn-text");
    const spinner = document.getElementById("spinner");
    const arrow = btn.querySelector(".btn-arrow");
    const respEl = document.getElementById("auth-response");

    btn.disabled = true;
    btnText.textContent = "Creating account…";
    spinner.classList.add("active");
    arrow.style.display = "none";

    const payload = {
      first_name: document.getElementById("first_name").value,
      last_name: document.getElementById("last_name").value,
      username: document.getElementById("username").value,
      email: document.getElementById("email").value,
      phone_number: document.getElementById("phone_number").value,
      password: pwInput.value,
      confirm_password: cfInput.value,
      role: "USER",
    };

    try {
      const res = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": await getCSRFToken(),
        },
        body: JSON.stringify(payload),
      });

      respEl.style.display = "block";

      if (res.status === 201) {
        respEl.style.cssText = `
          display:block;
          background: rgba(61,122,94,0.08);
          border: 1px solid rgba(61,122,94,0.25);
          color: #3d7a5e;
        `;
        respEl.textContent = "✓ Account created! Check your email to verify.";
        const form = document.getElementById("register-form");
        form.style.opacity = "0.4";
        form.style.pointerEvents = "none";
        setTimeout(
          () => (window.location.href = window.APP_CONFIG.loginUrl),
          2500,
        );
      } else {
        respEl.style.cssText = `
          display:block;
          background: rgba(201,74,42,0.08);
          border: 1px solid rgba(201,74,42,0.25);
          color: #c94a2a;
        `;
        try {
          const err = await res.json();

          let message = "Registration failed.";

          if (err.description) {
            message = err.description;
          } else if (err.message) {
            message = err.message;
          } else {
            const first = Object.values(err)[0];
            message =
              typeof first === "string"
                ? first
                : first?.message || JSON.stringify(first);
          }

          respEl.textContent = message;
        } catch (_) {
          respEl.textContent = "Registration failed. Please try again.";
        }
      }
    } catch (_) {
      respEl.style.cssText = `
        display:block;
        background: rgba(201,74,42,0.08);
        border: 1px solid rgba(201,74,42,0.25);
        color: #c94a2a;
      `;
      respEl.textContent = "Network error. Please try again.";
    } finally {
      btn.disabled = false;
      btnText.textContent = "Create Account";
      spinner.classList.remove("active");
      arrow.style.display = "";
    }
  });
