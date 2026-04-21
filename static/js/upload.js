import { getCSRFToken } from "./csrf.js";

const MAX_FILE_SIZE = 100 * 1024 * 1024,
  MAX_FILES = 10;
let fileList = [],
  detectedData = [],
  selectedFormats = {},
  detectionDone = false;

function getCookie(n) {
  const m = document.cookie.match(
    new RegExp(
      "(?:^|; )" + n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)",
    ),
  );
  return m ? decodeURIComponent(m[1]) : null;
}
async function getAuthHeaders() {
  const csrf = await getCSRFToken();
  const token = getCookie("access_token");

  const headers = {};
  if (csrf) headers["X-CSRF-Token"] = csrf;
  console.log(token);
  if (token) headers["Authorization"] = "Bearer " + token;

  return headers;
}
function getExt(fn) {
  return (
    ((fn || "").split(".").pop() || "").toUpperCase().slice(0, 6) || "FILE"
  );
}
function formatBytes(b) {
  if (!b) return "0 B";
  const k = 1024,
    s = ["B", "KB", "MB", "GB"],
    i = Math.floor(Math.log(b) / Math.log(k));
  return parseFloat((b / Math.pow(k, i)).toFixed(1)) + " " + s[i];
}
function showToast(msg, type = "info") {
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
async function refreshAccessToken() {
  try {
    const resp = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      credentials: "include",
      headers: await getAuthHeaders(),
    });

    if (resp.status === 401) {
      showToast("Session expired. Please log in again.", "error");
      setTimeout(() => {
        window.location.href = window.APP_CONFIG.loginUrl;
      }, 1500);
      return false;
    }

    if (!resp.ok) return false;

    return true;
  } catch {
    return false;
  }
}
function showError(msg) {
  const p = document.getElementById("errorPanel");
  p.textContent = msg;
  p.classList.add("show");
  setTimeout(() => p.classList.remove("show"), 5000);
}

function updateStats() {
  const sz = fileList.reduce((s, f) => s + f.size, 0);
  const exts = [...new Set(fileList.map((f) => getExt(f.name)))];
  document.getElementById("statFiles").textContent = fileList.length;
  document.getElementById("statSize").textContent = formatBytes(sz);
  if (!detectionDone)
    document.getElementById("statFormats").textContent = exts.length
      ? exts.slice(0, 3).join("/")
      : "--";
  // document.getElementById("detectBtn").disabled =
  //   fileList.length === 0 || detectionDone;
  document.getElementById("clearBtn").style.display =
    fileList.length > 0 ? "inline-flex" : "none";
}

function checkAllSelected() {
  if (!detectionDone) return;
  const eligible = detectedData.filter(
    (f) => (f.allowed_formats || []).length > 0,
  );
  const selCount = eligible.filter(
    (f, ii) => selectedFormats[detectedData.indexOf(f)],
  ).length;
  const allDone = eligible.length > 0 && selCount === eligible.length;
  document.getElementById("proceedBtn").disabled = !allDone;
  const hint = document.getElementById("proceedHint");
  hint.innerHTML = allDone
    ? '<span style="color:var(--success)">All set - ready to convert!</span>'
    : "<span>" +
      selCount +
      "/" +
      eligible.length +
      " file" +
      (eligible.length !== 1 ? "s" : "") +
      " configured</span>";
}

function selectFormat(idx, fmt, btn) {
  selectedFormats[idx] = fmt;

  document
    .querySelectorAll(".fg-" + idx + " .fmt-btn")
    .forEach((b) => b.classList.remove("selected"));

  btn.classList.add("selected");

  checkAllSelected();
}

function buildFileItemHTML(file, i, fromDetected) {
  const ext = getExt(file.filename || file.name || "file");
  const size = file.file_size || file.size || 0;
  const mime = file.mime || "";
  const ftype = file.file_type || "";
  const fmts = file.allowed_formats || [];
  let formatHTML = "";
  if (fromDetected) {
    if (fmts.length) {
      formatHTML =
        '<div class="format-panel show" id="fp-' +
        i +
        '"><div class="format-panel-label"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--accent2)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>Convert to</div><div class="fmt-grid fg-' +
        i +
        '">' +
        fmts
          .map(
            (f) =>
              `<button 
  class="fmt-btn ${selectedFormats[i] === f ? "selected" : ""}" 
  data-idx="${i}" 
  data-format="${f}">
  ${f.toUpperCase()}
</button>`,
          )
          .join("") +
        "</div></div>";
    } else {
      formatHTML =
        '<div class="format-panel show"><div class="no-formats">No conversions available for this file type.</div></div>';
    }
  }
  return (
    '<div class="file-item' +
    (fromDetected ? " detected" : "") +
    '" id="fi-' +
    i +
    '"><div class="file-item-top"><div class="file-icon">' +
    ext +
    '</div><div class="file-info"><div class="file-name">' +
    (file.filename || file.name || "Unknown") +
    '</div><div class="file-meta">' +
    formatBytes(size) +
    (mime ? " &middot; " + mime : "") +
    (ftype ? " &middot; " + ftype : "") +
    '</div><div class="progress-bar"><div class="progress-fill" id="pb-' +
    i +
    '" style="width:' +
    (fromDetected ? "100%" : "0%") +
    '"></div></div></div><div class="file-status ' +
    (fromDetected ? "status-detected" : "status-ready") +
    '" id="fs-' +
    i +
    '">' +
    (fromDetected ? "DETECTED" : "READY") +
    '</div><button class="file-remove" onclick="removeFile(' +
    i +
    ')" title="Remove"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 18L18 6M6 6l12 12"/></svg></button></div>' +
    formatHTML +
    "</div>"
  );
}

function renderQueue() {
  const q = document.getElementById("fileQueue");

  if (detectionDone) {
    q.innerHTML = detectedData
      .map((f, i) => buildFileItemHTML(f, i, true))
      .join("");
  } else {
    q.innerHTML = fileList
      .map((f, i) =>
        buildFileItemHTML(
          {
            filename: f.name,
            file_size: f.size,
            mime: "",
            file_type: "",
            allowed_formats: [],
          },
          i,
          false,
        ),
      )
      .join("");
  }

  // 🔥 ADD IT RIGHT HERE
  document.querySelectorAll(".fmt-btn").forEach((btn) => {
    btn.addEventListener("click", function () {
      const idx = parseInt(this.dataset.idx);
      const fmt = this.dataset.format;

      selectFormat(idx, fmt, this);
    });
  });

  updateStats();
}

function addFiles(files) {
  if (detectionDone) resetDetection();
  const errs = [];

  Array.from(files).forEach((f) => {
    if (fileList.length >= MAX_FILES) {
      errs.push("Max " + MAX_FILES + " files allowed");
      return;
    }
    if (f.size > MAX_FILE_SIZE) {
      errs.push(f.name + " exceeds 100MB");
      return;
    }
    if (fileList.find((x) => x.name === f.name && x.size === f.size)) {
      errs.push(f.name + " already queued");
      return;
    }
    fileList.push(f);
  });

  if (errs.length) showError(errs[0]);

  renderQueue();

  if (fileList.length > 0) {
    uploadAndDetect();
  }
}

function removeFile(i) {
  fileList.splice(i, 1);
  if (detectionDone) {
    detectedData.splice(i, 1);
    const ns = {};
    Object.entries(selectedFormats).forEach(([k, v]) => {
      const nk = parseInt(k);
      if (nk < i) ns[nk] = v;
      else if (nk > i) ns[nk - 1] = v;
    });
    selectedFormats = ns;
    if (!detectedData.length) resetDetection();
  }
  renderQueue();
  if (detectionDone) checkAllSelected();
}

function clearAll() {
  fileList = [];
  detectedData = [];
  selectedFormats = {};
  resetDetection();
  renderQueue();
}

// function resetDetection() {
//   detectionDone = false;
//   // document.getElementById("detectBtn").disabled = fileList.length === 0;
//   // document.getElementById("detectBtn").style.opacity = "1";
//   document.getElementById("proceedBar").classList.remove("show");
// }
function resetDetection() {
  detectionDone = false;
  document.getElementById("proceedBar").classList.remove("show");
}
const zone = document.getElementById("uploadZone");
zone.addEventListener("dragover", (e) => {
  e.preventDefault();
  zone.classList.add("drag-over");
});
zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));
zone.addEventListener("drop", (e) => {
  e.preventDefault();
  zone.classList.remove("drag-over");
  addFiles(e.dataTransfer.files);
});
zone.addEventListener("click", () =>
  document.getElementById("fileInput").click(),
);
document.getElementById("fileInput").addEventListener("change", (e) => {
  addFiles(e.target.files);
  e.target.value = "";
});
async function apiFetch(url, options = {}) {
  options.credentials = "include";

  const authHeaders = await getAuthHeaders();
  options.headers = { ...authHeaders, ...(options.headers || {}) };

  let resp = await fetch(url, options);

  if (resp.status === 401) {
    const refreshed = await refreshAccessToken();
    if (!refreshed) return resp;

    const newHeaders = await getAuthHeaders();
    options.headers = { ...newHeaders, ...(options.headers || {}) };

    resp = await fetch(url, options);
  }

  return resp;
}
async function uploadAndDetect() {
  if (!fileList.length) return;

  const overlay = document.getElementById("loaderOverlay");
  document.getElementById("loaderText").textContent =
    "Uploading & detecting...";
  document.getElementById("loaderSub").textContent = "Reading file signatures";
  overlay.classList.add("show");
  fileList.forEach((_, i) => {
    const fs = document.getElementById("fs-" + i);
    if (fs) {
      fs.className = "file-status status-uploading";
      fs.textContent = "UPLOADING";
    }
  });
  try {
    const fd = new FormData();
    fileList.forEach((f) => fd.append("file", f));

    let prog = 0;
    const pi = setInterval(() => {
      prog = Math.min(prog + Math.random() * 14, 82);
      fileList.forEach((_, i) => {
        const pb = document.getElementById("pb-" + i);
        if (pb) pb.style.width = prog + "%";
      });
    }, 180);
    const resp = await apiFetch("/api/v1/detect/files", {
      method: "POST",
      body: fd,
    });
    clearInterval(pi);
    if (!resp.ok) {
      const e = await resp.json().catch(() => ({ error: "Upload failed" }));
      throw new Error(e.error || "Error " + resp.status);
    }
    const data = await resp.json();
    const detected = data.files || [];
    if (!detected.length) throw new Error("No files were detected");
    detectedData = detected;
    detectionDone = true;
    selectedFormats = {};
    // document.getElementById("detectBtn").disabled = true;
    // document.getElementById("detectBtn").style.opacity = "0.35";
    document.getElementById("proceedBar").classList.add("show");
    const types = [
      ...new Set(detected.map((f) => f.file_type || "").filter(Boolean)),
    ];
    document.getElementById("statFormats").textContent =
      types.slice(0, 3).join("/") || "--";
    overlay.classList.remove("show");
    showToast(
      detected.length +
        " file" +
        (detected.length !== 1 ? "s" : "") +
        " ready - select formats below",
      "success",
    );
    renderQueue();
    checkAllSelected();
  } catch (err) {
    overlay.classList.remove("show");
    fileList.forEach((_, i) => {
      const fs = document.getElementById("fs-" + i);
      if (fs) {
        fs.className = "file-status status-error";
        fs.textContent = "ERROR";
      }
    });
    showError(err.message || "Upload failed. Please try again.");
    showToast(err.message || "Upload failed", "error");
  }
}

async function proceedToConversion() {
  const missing = detectedData.findIndex(
    (f, i) => (f.allowed_formats || []).length > 0 && !selectedFormats[i],
  );
  if (missing !== -1) {
    showError("Please select an output format for every file.");
    return;
  }
  const overlay = document.getElementById("loaderOverlay");
  document.getElementById("loaderText").textContent = "Starting conversion...";
  document.getElementById("loaderSub").textContent = "Preparing your files";
  overlay.classList.add("show");
  try {
    for (let i = 0; i < detectedData.length; i++) {
      const file = detectedData[i];
      const outputFmt = selectedFormats[i];

      // Skip files with no available conversion formats
      if ((file.allowed_formats || []).length === 0) {
        continue;
      }

      const resp = await apiFetch("/api/v1/start/conversion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          temp_file_id: file.temp_file_id,
          mime: file.mime,
          file_type: file.file_type,
          output_format: outputFmt,
          filename: file.filename,
        }),
      });

      const result = await resp.json();
      if (!resp.ok) {
        throw new Error(result.error || `Failed to convert ${file.filename}`);
      }

      // Use the filename returned from the conversion response
      const convertedFilename = result.filename;

      showToast("Conversion started successfully", "success");

      setTimeout(
        async () => {
          try {
            const resp = await apiFetch(
              `/api/v1/media/converted/${encodeURIComponent(convertedFilename)}`,
            );

            if (!resp.ok)
              throw new Error("Download failed or Conversion not ready");

            const blob = await resp.blob();
            const url = window.URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = convertedFilename;
            document.body.appendChild(a);
            a.click();
            a.remove();

            window.URL.revokeObjectURL(url);
          } catch (err) {
            console.error(err);
          }
        },
        (i + 1) * 800,
      );
    }
    setTimeout(
      () => {
        overlay.classList.remove("show");
        window.location.href = window.APP_CONFIG.homeUrl;
      },
      (detectedData.length + 2) * 800,
    );
  } catch (err) {
    overlay.classList.remove("show");
    showError(err.message || "Conversion failed");
    showToast(err.message || "Conversion failed", "error");
  }
}
async function checkAuth() {
  try {
    const resp = await fetch("/api/v1/auth/me", {
      credentials: "include",
      "X-CSRFToken": await getCSRFToken(),
    });

    return resp.ok;
  } catch {
    return false;
  }
}
async function toggleAuthUI() {
  const isLoggedIn = await checkAuth();

  const loginLink = document.getElementById("loginLink");
  const signupLink = document.getElementById("signupLink");
  const logoutLink = document.getElementById("logoutLink");
  const myFilesLink = document.getElementById("myFilesLink");

  if (isLoggedIn) {
    loginLink.style.display = "none";
    signupLink.style.display = "none";

    logoutLink.style.display = "inline-flex";
    myFilesLink.style.display = "inline-flex";
  } else {
    loginLink.style.display = "inline-flex";
    signupLink.style.display = "inline-flex";

    logoutLink.style.display = "none";
    myFilesLink.style.display = "none";
  }
}
document.addEventListener("DOMContentLoaded", async () => {
  await toggleAuthUI();

  
  document.getElementById("fileQueue").addEventListener("click", (e) => {
    if (e.target.classList.contains("fmt-btn")) {
      const idx = parseInt(e.target.dataset.idx);
      const fmt = e.target.dataset.format;

      selectFormat(idx, fmt, e.target);
    }
  });

  document.getElementById("clearBtn").addEventListener("click", clearAll);

  document
    .getElementById("proceedBtn")
    .addEventListener("click", proceedToConversion);

  document.getElementById("logoutLink").addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const resp = await apiFetch("/api/v1/auth/logout", {
        method: "POST",
      });

      if (resp.ok) {
        showToast("Logged out successfully", "success");
        await toggleAuthUI();
        setTimeout(() => {
          window.location.href = window.APP_CONFIG.homeUrl;
        }, 1000);
      }
    } catch {
      showToast("Logout failed", "error");
    }
  });
});
window.selectFormat = selectFormat;
window.removeFile = removeFile;
