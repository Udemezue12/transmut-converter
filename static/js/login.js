import { getCSRFToken } from "./csrf.js";


const pwInput = document.getElementById("password");
const toggleBtn = document.getElementById("toggle-pw-btn");
let pwShown = false;

toggleBtn.addEventListener("click", () => {
  pwShown = !pwShown;
  pwInput.type = pwShown ? "text" : "password";
  toggleBtn.textContent = pwShown ? "hide" : "show";
});

document.querySelectorAll("input").forEach((inp) => {
  inp.addEventListener("focus", () =>
    inp
      .closest(".field")
      ?.querySelector("label")
      ?.style.setProperty("color", "var(--ink-2)"),
  );
  inp.addEventListener("blur", () =>
    inp
      .closest(".field")
      ?.querySelector("label")
      ?.style.setProperty("color", "var(--ink-4)"),
  );
});


function shakeForm() {
  document
    .getElementById("login-form")
    .animate(
      [
        { transform: "translateX(-6px)" },
        { transform: "translateX(6px)" },
        { transform: "translateX(-4px)" },
        { transform: "translateX(4px)" },
        { transform: "translateX(0)" },
      ],
      { duration: 350, easing: "ease-out" },
    );
}


document
  .getElementById("login-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const btn = document.getElementById("login-btn");
    const btnText = document.getElementById("login-btn-text");
    const spinner = document.getElementById("login-spinner");
    const arrow = btn.querySelector(".btn-arrow");
    const respEl = document.getElementById("auth-response");

    
    btn.disabled = true;
    btnText.textContent = "Signing in…";
    spinner.classList.add("active");
    arrow.style.display = "none";
    respEl.style.display = "none";

    const payload = {
      email: document.getElementById("email").value.trim(),
      password: pwInput.value,
    };

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": await getCSRFToken(),
        },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();

        
        if (data.user) {
          localStorage.setItem("transmute_user", JSON.stringify(data.user));
        }

        setTimeout(
          () => (window.location.href = window.APP_CONFIG.homeUrl),
          2500,
        );
      } else {
        respEl.style.display = "block";
        try {
          const err = await res.json();
          respEl.textContent =
            "✕ " +
            (err.detail || err.non_field_errors?.[0] || "Invalid credentials.");
        } catch (_) {
          respEl.textContent = "✕ Invalid credentials.";
        }
        shakeForm();
      }
    } catch (_) {
      respEl.style.display = "block";
      respEl.textContent = "✕ Network error. Please try again.";
      shakeForm();
    } finally {
      btn.disabled = false;
      btnText.textContent = "Sign In";
      spinner.classList.remove("active");
      arrow.style.display = "";
    }
  });
