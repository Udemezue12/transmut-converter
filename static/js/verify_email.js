import { getCSRFToken } from "./csrf.js";

const msgBox = document.getElementById("msg");
const modalMsg = document.getElementById("modalMsg");

const otpInput = document.getElementById("otpInput");
const verifyBtn = document.getElementById("verifyBtn");

const resendBtn = document.getElementById("resendBtn");
const resendModal = document.getElementById("resendModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const sendResendBtn = document.getElementById("sendResendBtn");

const modalEmailInput = document.getElementById("modalEmailInput");
const timerEl = document.getElementById("timer");

// ------------------
// UTIL
// ------------------

function showMessage(el, text) {
  el.style.display = "block";
  el.textContent = text;
}

function hideMessage(el) {
  el.style.display = "none";
  el.textContent = "";
}

function disableBtn(btn, text = "Processing...") {
  btn.disabled = true;
  btn.dataset.original = btn.innerHTML;
  btn.innerHTML = `<span>${text}</span>`;
}

function enableBtn(btn) {
  btn.disabled = false;
  btn.innerHTML = btn.dataset.original;
}

async function verifyEmail() {
  hideMessage(msgBox);

  const otp = otpInput.value.trim();

  if (!otp || otp.length !== 6) {
    return showMessage(msgBox, "Enter a valid 6-digit OTP");
  }

  disableBtn(verifyBtn);

  try {
    const res = await fetch("/api/v1/auth/verify-email", {
      method: "POST",
      headers: {
        "X-CSRF-Token": await getCSRFToken(),
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({ otp }),
    });

    const data = await res.json();

    if (!resp.ok) {
      showMessage(
        msgBox,
        data.description || data.error || "Verification failed",
      );
      return;
    }

    showMessage(msgBox, data.message || "Email verified");

    // redirect after success
    setTimeout(() => {
      window.location.href = window.APP_CONFIG.loginUrl;
    }, 1500);
  } catch (err) {
    showMessage(msgBox, "Network error. Try again.");
  } finally {
    enableBtn(verifyBtn);
  }
}

// ------------------
// TOKEN AUTO VERIFY (from URL)
// ------------------

async function autoVerifyFromToken() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  if (!token) return;

  disableBtn(verifyBtn, "Verifying...");

  try {
    const res = await fetch("/api/v1/auth/verify-email", {
      method: "POST",
      headers: {
        "X-CSRF-Token": await getCSRFToken(),
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify({ token }),
    });

    const data = await res.json();

    showMessage(msgBox, data.message || "Verification complete");

    setTimeout(() => {
      window.location.href = window.APP_CONFIG.loginUrl;
    }, 1500);
  } catch {
    showMessage(msgBox, "Invalid or expired link");
  } finally {
    enableBtn(verifyBtn);
  }
}

// ------------------
// RESEND MODAL
// ------------------

function openModal() {
  resendModal.classList.add("open");
}

function closeModal() {
  resendModal.classList.remove("open");
  modalEmailInput.value = "";
  hideMessage(modalMsg);
}

// ------------------
// RESEND EMAIL
// ------------------

async function resendVerification() {
  hideMessage(modalMsg);

  const email = modalEmailInput.value.trim();

  if (!email) {
    return showMessage(modalMsg, "Enter your email");
  }

  disableBtn(sendResendBtn, "Sending...");

  try {
    const res = await fetch("/api/v1/auth/resend_verification_email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": await getCSRFToken(),
      },
      body: JSON.stringify({ email: email }),
    });

    const data = await res.json();

    if (!resp.ok) {
      showMessage(modalMsg, data.description || "Failed to resend");
      return;
    }

    showMessage(modalMsg, data.message);

    startCooldown(60); // match backend cooldown
  } catch {
    showMessage(modalMsg, "Network error");
  } finally {
    enableBtn(sendResendBtn);
  }
}

// ------------------
// TIMER (cooldown UI)
// ------------------

let countdown = null;

function startCooldown(seconds) {
  clearInterval(countdown);

  let remaining = seconds;

  resendBtn.disabled = true;

  countdown = setInterval(() => {
    timerEl.textContent = `Resend available in ${remaining}s`;

    remaining--;

    if (remaining <= 0) {
      clearInterval(countdown);
      resendBtn.disabled = false;
      timerEl.textContent = "";
    }
  }, 1000);
}

// ------------------
// EVENTS
// ------------------

verifyBtn.addEventListener("click", verifyEmail);

otpInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") verifyEmail();
});

resendBtn.addEventListener("click", openModal);
closeModalBtn.addEventListener("click", closeModal);

sendResendBtn.addEventListener("click", resendVerification);

// close modal on outside click
resendModal.addEventListener("click", (e) => {
  if (e.target === resendModal) closeModal();
});

// ------------------
// INIT
// ------------------

autoVerifyFromToken();
