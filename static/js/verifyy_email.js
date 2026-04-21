import { getCSRFToken } from "./csrf.js";

const params = new URLSearchParams(window.location.search);
let token = params.get("token");
let emailParam = params.get("email");


if (!emailParam || emailParam.trim() === "") {
  emailParam = null;
}

const emailWrapper = document.getElementById("emailWrapper");
const emailInput = document.getElementById("emailInput");
const otpInput = document.getElementById("otpInput");
const verifyBtn = document.getElementById("verifyBtn");
const resendBtn = document.getElementById("resendBtn");
const timerEl = document.getElementById("timer");
const msg = document.getElementById("msg");
const resendModal = document.getElementById("resendModal");
const modalEmailInput = document.getElementById("modalEmailInput");
const sendResendBtn = document.getElementById("sendResendBtn");
const closeModalBtn = document.getElementById("closeModalBtn");
const modalMsg = document.getElementById("modalMsg");

let resendAttempts = 0;
let cooldownInterval = null;

if (!emailParam) {
  emailWrapper.style.display = "block";
} else {
  emailWrapper.style.display = "none";
  emailInput.value = emailParam;
}
closeModalBtn.onclick = () => {
  resendModal.style.display = "none";
  modalMsg.textContent = "";
};

async function autoVerify(tokenValue) {
  showInfo("Verifying your email...");

  try {
    const res = await fetch("/api/v1/auth/verify-email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": await getCSRFToken(),
      },
      //   credentials: "include",
      body: JSON.stringify({ token: tokenValue }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Verification failed");

    showSuccess("Email verified successfully!");
    setTimeout(() => (window.location.href = window.APP_CONFIG.loginUrl), 1500);
  } catch (err) {
    showError(err.message);
  }
}

if (token) {
  await autoVerify(token);
}

/* =============================
         MANUAL VERIFY (OTP MODE)
      ============================= */

verifyBtn.onclick = async () => {
  const payload = {};

  if (token) {
    payload.token = token;
  } else if (otpInput.value.trim()) {
    payload.otp = otpInput.value.trim();
  }

  if (!payload.token && !payload.otp) {
    showError("Enter OTP or use verification link.");
    return;
  }

  verifyBtn.disabled = true;

  try {
    const res = await fetch("/api/v1/auth/verify-email", {
      method: "POST",

      headers: {
        "X-CSRFToken": await getCSRFToken(),
        "Content-Type": "application/json",
      },
      //credentials: "include",
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Verification failed");

    showSuccess("Email verified successfully!");
    setTimeout(() => (window.location.href = window.APP_CONFIG.loginUrl), 1500);
  } catch (err) {
    showError(err.message);
  } finally {
    verifyBtn.disabled = false;
  }
};

sendResendBtn.onclick = async () => {
  const userEmail = modalEmailInput.value.trim();

  if (!userEmail) {
    modalMsg.textContent = "Please enter your email.";
    return;
  }

  sendResendBtn.disabled = true;

  try {
    const res = await fetch("/api/v1/auth/resend_verification_email", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": await getCSRFToken(),
      },
      body: JSON.stringify({ email: userEmail }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to resend email");

    modalMsg.textContent = "Verification email sent!";
    resendAttempts++;
    startCooldown();

    // Optional: close after success
    setTimeout(() => {
      resendModal.style.display = "none";
      modalMsg.textContent = "";
    }, 1500);
  } catch (err) {
    modalMsg.textContent = err.message;
  } finally {
    sendResendBtn.disabled = false;
  }
};
window.onclick = (e) => {
  if (e.target === resendModal) {
    resendModal.style.display = "none";
    modalMsg.textContent = "";
  }
};
function startCooldown() {
  let duration = resendAttempts >= 3 ? 3600 : 30;
  let remaining = duration;

  timerEl.textContent = `You can resend again in ${remaining}s`;
  if (cooldownInterval) clearInterval(cooldownInterval);

  cooldownInterval = setInterval(() => {
    remaining--;
    timerEl.textContent = `You can resend again in ${remaining}s`;

    if (remaining <= 0) {
      clearInterval(cooldownInterval);
      resendBtn.disabled = false;
      timerEl.textContent = "";
    }
  }, 1000);
}

/* =============================
         UI HELPERS
      ============================= */

function showError(text) {
  msg.textContent = text;
  msg.className = "error";
}

function showSuccess(text) {
  msg.textContent = text;
  msg.className = "success";
}

function showInfo(text) {
  msg.textContent = text;
  msg.className = "";
}
