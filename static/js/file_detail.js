
import { apiFetch } from "./fetchApi.js";


function getCookie(name) {
  const match = document.cookie.match(
    new RegExp("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)"),
  );
  return match ? decodeURIComponent(match[2]) : null;
}

function showToast(msg, ok = true) {
  const wrap = document.getElementById("toastWrap");
  const t = document.createElement("div");
  t.className = "toast";
  t.innerHTML = `<span style="color:${ok ? "var(--success)" : "var(--danger)"};font-size:16px">${ok ? "✓" : "✕"}</span> ${msg}`;
  wrap.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function iconType(fileType) {
  const t = (fileType || "").toLowerCase();
  if (t.includes("image")) return ["t-image", "IMG"];
  if (t.includes("video")) return ["t-video", "VID"];
  if (t.includes("audio")) return ["t-audio", "AUD"];
  return ["t-doc", "DOC"];
}

function statusBadge(status) {
  const map = {
    completed: ["done", "completed"],
    pending: ["pending", "pending"],
    failed: ["failed", "failed"],
    processing: ["proc", "processing"],
  };
  const [cls, label] = map[(status || "").toLowerCase()] || [
    "pending",
    "pending",
  ];
  return `<span class="badge ${cls}"><span class="badge-dot"></span>${label}</span>`;
}

function clearSkeletons(...ids) {
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.classList.remove("skeleton");
  });
}


function getPageContext() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  
  if (parts[0] === "uploaded" && parts[1])
    return { mode: "upload", id: parts[1] };
  if (parts[0] === "converted" && parts[1])
    return { mode: "conversion", id: parts[1] };
  return null;
}


async function fetchUpload(uploadId) {
  const res = await apiFetch(`/api/v1/uploaded/${uploadId}/file`);

  if (!res) return null;

  if (!res.ok) {
    throw new Error(`Conversion fetch failed (${res.status})`);
  }

  return res.json();
}

async function fetchConversion(conversionId) {
  const res = await apiFetch(`/api/v1/converted/${conversionId}/file`);

  if (!res) return null;

  if (!res.ok) {
    throw new Error(`Conversion fetch failed (${res.status})`);
  }

  return res.json();
}

function renderUploadOnly(upload) {
  clearSkeletons("origIcon", "origName", "origMime");

  const [cls, label] = iconType(upload.file_type);
  document.getElementById("origIcon").className = `hero-icon ${cls}`;
  document.getElementById("origIcon").textContent = label;

  document.getElementById("origName").className = "hero-filename";
  document.getElementById("origName").textContent = upload.original_filename;

  document.getElementById("origMime").className = "hero-mime";
  document.getElementById("origMime").textContent =
    upload.detected_mime || upload.file_type || "—";

  document.getElementById("origMeta").innerHTML = `
    <tr><td>file id</td>
        <td style="font-family:'DM Mono',monospace;font-size:11px;word-break:break-all">${upload.id}</td></tr>
    <tr><td>uploaded</td><td>${fmtDate(upload.created_at)}</td></tr>
    <tr><td>type</td><td>${upload.file_type || "—"}</td></tr>
    <tr><td>mime</td><td>${upload.detected_mime || "—"}</td></tr>
    ${
      upload.cloudinary_file_url
        ? `
    <tr><td>source</td><td>
      <a href="${upload.cloudinary_file_url}" target="_blank" rel="noopener"
         style="font-size:11px;word-break:break-all;color:var(--accent)">
        view original
      </a>
    </td></tr>`
        : ""
    }
  `;

  hide("convPanel", "heroArrow", "convListSection");
}

function renderConversionOnly(upload, conversion) {
 
  clearSkeletons("origIcon", "origName", "origMime");

  const [origCls, origLabel] = iconType(upload.file_type);
  document.getElementById("origIcon").className = `hero-icon ${origCls}`;
  document.getElementById("origIcon").textContent = origLabel;

  document.getElementById("origName").className = "hero-filename";
  document.getElementById("origName").textContent = upload.original_filename;

  document.getElementById("origMime").className = "hero-mime";
  document.getElementById("origMime").textContent =
    upload.detected_mime || upload.file_type || "—";

  document.getElementById("origMeta").innerHTML = `
    <tr><td>uploaded</td><td>${fmtDate(upload.created_at)}</td></tr>
    <tr><td>type</td><td>${upload.file_type || "—"}</td></tr>
    <tr><td>mime</td><td>${upload.detected_mime || "—"}</td></tr>
  `;

  clearSkeletons("convIcon", "convName", "convStatus");

  const convFmt =
    (conversion.output_format || "").toUpperCase().slice(0, 3) || "OUT";
  const ext = (conversion.output_format || "bin").toLowerCase();
  const baseName = upload.original_filename.replace(/\.[^.]+$/, "");
  const convFilename = `${baseName}.${ext}`;

  document.getElementById("convIcon").className = "hero-icon t-doc";
  document.getElementById("convIcon").textContent = convFmt;

  document.getElementById("convName").className = "hero-filename";
  document.getElementById("convName").textContent = convFilename;

  const convStatusEl = document.getElementById("convStatus");
  if (convStatusEl) convStatusEl.outerHTML = statusBadge(conversion.status);

  document.getElementById("convMeta").innerHTML = `
    <tr><td>conv id</td>
        <td style="font-family:'DM Mono',monospace;font-size:11px;word-break:break-all">${conversion.id}</td></tr>
    <tr><td>format</td><td>${conversion.output_format || "—"}</td></tr>
    <tr><td>status</td><td>${statusBadge(conversion.status)}</td></tr>
    <tr><td>completed</td><td>${fmtDate(conversion.completed_at)}</td></tr>
    ${
      conversion.error_message
        ? `<tr><td>error</td><td style="color:var(--danger);font-size:12px">${conversion.error_message}</td></tr>`
        : ""
    }
    ${
      conversion.result_cloudinary_url && conversion.status === "completed"
        ? `
    <tr><td>download</td><td>
      <button class="action-btn download"
              onclick="downloadFile('${conversion.result_cloudinary_url}','${convFilename}')">
        <svg width="11" height="11" viewBox="0 0 16 16" fill="none"
             stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M8 2v9M4 11l4 4 4-4"/><path d="M2 14h12"/>
        </svg>
        Download
      </button>
    </td></tr>`
        : ""
    }
  `;

  hide("convListSection");
}

function hide(...ids) {
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  });
}


async function load() {
  const ctx = getPageContext();
  if (!ctx) {
    window.location.href = "/";
    return;
  }

  try {
    if (ctx.mode === "upload") {
      const upload = await fetchUpload(ctx.id);
      if (!upload) return;

      document.title = `${upload.original_filename} — Transmute`;
      window.__uploadId = upload.id;

      setAvatar();
      renderUploadOnly(upload);
    } else if (ctx.mode === "conversion") {
      const conversion = await fetchConversion(ctx.id);
      if (!conversion) return;

      const upload = await fetchUpload(conversion.upload_id);
      if (!upload) return;

      document.title = `${upload.original_filename} → ${(conversion.output_format || "").toUpperCase()} — Transmute`;
      window.__uploadId = upload.id;
      window.__conversionId = conversion.id;

      setAvatar();
      renderConversionOnly(upload, conversion);
    }
  } catch (e) {
    console.error(e);
    showToast(e.message || "Failed to load file details", false);
  }
}

function setAvatar() {
  const raw = localStorage.getItem("transmute_user");
  if (!raw) return;
  try {
    const user = JSON.parse(raw);
    const initials = (user.email || user.username || "??")
      .slice(0, 2)
      .toUpperCase();
    document.getElementById("userAvatar").textContent = initials;
  } catch (_) {}
}

function openModal() {
  document.getElementById("deleteModal").classList.add("open");
}
function closeModal() {
  document.getElementById("deleteModal").classList.remove("open");
}
async function confirmDelete() {
  closeModal();
  const res = await apiFetch(`/api/v1/uploaded/${window.__uploadId}/delete`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });
  if (!res) return; 
  if (!res.ok) {
    showToast("Delete failed", false);
    return;
  }
  showToast("File deleted");
  setTimeout(() => {
    window.location.href = window.APP_CONFIG.filesUrl;
  }, 1200);
}

function downloadFile(url, name) {
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.target = "_blank";
  a.click();
}

window.openModal = openModal;
window.closeModal = closeModal;
window.confirmDelete = confirmDelete;
window.downloadFile = downloadFile;

(async () => {
  await load();
})();
