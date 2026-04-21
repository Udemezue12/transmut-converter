import { getCSRFToken } from "./csrf.js";

let cooldownTimer = null;
let cooldownRemaining = 0;

function showResponse(message, ok = true) {
  const el = document.getElementById("auth-response");
  if (!el) return;

  el.style.display = "block";
  el.textContent = message;
  el.style.borderLeftColor = ok ? "#4caf7d" : "#c94c4c";
}

function setLoading(state) {
  const btn = document.getElementById("forgot-btn");
  const text = document.getElementById("forgot-btn-text");

  if (!btn || !text) return;

  btn.disabled = state;
  text.textContent = state ? "Sending..." : "Send Reset Link";
}


function startCooldown(seconds = 10) {
  const btn = document.getElementById("forgot-btn");
  const text = document.getElementById("forgot-btn-text");

  if (!btn || !text) return;

  cooldownRemaining = seconds;
  btn.disabled = true;

  text.textContent = `Wait ${cooldownRemaining}s`;

  cooldownTimer = setInterval(() => {
    cooldownRemaining--;

    if (cooldownRemaining > 0) {
      text.textContent = `Wait ${cooldownRemaining}s`;
    } else {
      clearInterval(cooldownTimer);
      cooldownTimer = null;

      btn.disabled = false;
      text.textContent = "Send Reset Link";
    }
  }, 1000);
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("forgot-form");
  const emailInput = document.getElementById("email");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

  
    if (cooldownTimer) {
      return showResponse(`Please wait ${cooldownRemaining}s before retrying.`, false);
    }

    const email = emailInput.value.trim();

    if (!email) {
      return showResponse("Email is required.", false);
    }

    if (!isValidEmail(email)) {
      return showResponse("Enter a valid email address.", false);
    }

    try {
      setLoading(true);
      showResponse("", true);

      const res = await fetch("/api/v1/auth/forgot_password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          data?.description ||
          data?.message ||
          (res.status === 404
            ? "Email not found."
            : res.status === 429
            ? "Too many requests. Try again shortly."
            : "Failed to send reset link.")
        );
      }

      showResponse(
        "Reset instructions sent. Check your email (and OTP if enabled).",
        true
      );

      form.reset();
      emailInput.blur();

     
      startCooldown(data.retry_after || 60);

    } catch (err) {
      showResponse(err.message || "Something went wrong.", false);

     
      if (err.message.toLowerCase().includes("too many")) {
        startCooldown(10);
      }

    } finally {
      setLoading(false);
    }
  });
});