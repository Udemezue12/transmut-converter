import { getCSRFToken } from "./csrf.js";

function showResponse(message, ok = true) {
  const el = document.getElementById("auth-response");
  if (!el) return;

  el.style.display = "block";
  el.textContent = message;
  el.style.borderLeftColor = ok ? "#4caf7d" : "#c94c4c";
}

function setLoading(state) {
  const btn = document.getElementById("reset-btn");
  const text = document.getElementById("reset-btn-text");

  if (!btn || !text) return;

  btn.disabled = state;
  text.textContent = state ? "Processing..." : "Reset Password";
}

function getQueryParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("reset-form");
  const tokenInput = document.getElementById("token-input");
  const otpInput = document.getElementById("otp-input");

  const newPassword = document.getElementById("new-password");
  const confirmPassword = document.getElementById("confirm-new-password");

  // 🔐 Extract token from URL
  const token = getQueryParam("token");

  if (token && tokenInput) {
    tokenInput.value = token;

    // If token exists → hide OTP field (optional UX improvement)
    const otpField = document.getElementById("otp-field");
    if (otpField) otpField.style.display = "none";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    showResponse("", true);

    const payload = {
      token: tokenInput.value || null,
      otp: otpInput?.value || null,
      new_password: newPassword.value,
      confirm_password: confirmPassword.value,
    };

    // 🔴 Frontend validation
    if (!payload.token && !payload.otp) {
      return showResponse("Provide OTP or reset token.", false);
    }

    if (payload.otp && payload.otp.length !== 6) {
      return showResponse("OTP must be 6 digits.", false);
    }

    if (payload.new_password.length < 8) {
      return showResponse("Password must be at least 8 characters.", false);
    }

    if (payload.new_password !== payload.confirm_password) {
      return showResponse("Passwords do not match.", false);
    }

    try {
      setLoading(true);

      const res = await fetch("/api/v1/auth/reset_password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": await getCSRFToken(),
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.description || data?.message || "Reset failed");
      }

      showResponse(data.message || "Password reset successful", true);

      setTimeout(() => {
        window.location.href = window.APP_CONFIG?.loginUrl || "/login";
      }, 1500);
    } catch (err) {
      showResponse(err.message || "Something went wrong", false);
    } finally {
      setLoading(false);
    }
  });

  // 🔢 Force OTP numeric only
  if (otpInput) {
    otpInput.addEventListener("input", () => {
      otpInput.value = otpInput.value.replace(/\D/g, "").slice(0, 6);
    });
  }
});
