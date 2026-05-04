import { apiFetch } from "./fetchApi.js";
import { getCookie } from "./cookies.js";


function showToast(msg, ok = true) {
  const wrap = document.getElementById("toastWrap");
  const t = document.createElement("div");
  t.className = "toast";
  t.innerHTML = `<span style="color:${ok ? "var(--success)" : "var(--danger)"};font-size:16px">${ok ? "✓" : "✕"}</span> ${msg}`;
  wrap.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}


let currentPage = 1;
const perPage = 10;
let allRows = [];
let activeFilter = "all";
let pendingDelete = null;

async function fetchConversions(page = 1) {
  const res = await apiFetch(
    `/api/v1/converted/files?page=${page}&per_page=${perPage}`,
  );
  if (!res) return null;
  if (!res.ok) {
    showToast("Failed to load files", false);
    return null;
  }
  return res.json();
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function iconClass(fileType) {
  const t = (fileType || "").toLowerCase();
  if (t.includes("image")) return "icon-image";
  if (t.includes("video")) return "icon-video";
  if (t.includes("audio")) return "icon-audio";
  return "icon-doc";
}

function iconLabel(fileType) {
  const t = (fileType || "").toLowerCase();
  if (t.includes("image")) return "IMG";
  if (t.includes("video")) return "VID";
  if (t.includes("audio")) return "AUD";
  return "DOC";
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

function loadUserFromStorage() {
  const raw = localStorage.getItem("transmute_user");
  if (!raw) return;

  try {
    const user = JSON.parse(raw);

    const email = user.username || "—";
    const initials = email.slice(0, 2).toUpperCase();

    document.getElementById("navEmail").textContent = email;
    document.getElementById("navAvatar").textContent = initials;
  } catch (e) {
    console.error("Failed to parse user");
  }
}
function renderCard(conversion) {
  const upload = conversion.upload;
  const convFmt = (conversion.output_format || "OUT").toUpperCase().slice(0, 3);
  const convFilename =
    upload.original_filename.replace(/\.[^.]+$/, "") +
    "." +
    (conversion.output_format || "").toLowerCase();

  const showDl =
    conversion.status === "completed" && conversion.result_cloudinary_url;

  return `
  <div class="pair-card" data-status="${(conversion.status || "pending").toLowerCase()}">
    <div class="pair-inner">

      <!-- ORIGINAL — clickable, navigates to upload detail -->
      <div class="file-panel original clickable"
           onclick="viewUpload('${upload.id}')"
           title="View upload details">
        <div class="panel-label orig-label">
          <span class="panel-dot orig-dot"></span>original
        </div>
        <div class="file-meta">
          <div class="file-icon ${iconClass(upload.file_type)}">${iconLabel(upload.file_type)}</div>
          <div class="file-info">
            <div class="file-name" title="${upload.original_filename}">${upload.original_filename}</div>
            <div class="file-detail">${upload.detected_mime || upload.file_type || "—"}</div>
          </div>
        </div>
        <div class="status-row">
          <span class="badge done"><span class="badge-dot"></span>uploaded</span>
          <span class="ts-small">${fmtDate(upload.created_at)}</span>
        </div>
        <div class="hover-hint">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="8" cy="8" r="6"/><path d="M8 6v4M8 11v.5"/>
          </svg>
          View details
        </div>
      </div>

      <!-- ARROW -->
      <div class="pair-arrow">
        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 8h10M9 4l4 4-4 4"/>
        </svg>
      </div>

      <!-- CONVERTED — clickable, navigates to conversion detail -->
      <div class="file-panel converted clickable"
           onclick="viewConversion('${conversion.id}')"
           title="View conversion details">
        <div class="panel-label conv-label">
          <span class="panel-dot conv-dot"></span>converted
        </div>
        <div class="file-meta">
          <div class="file-icon icon-doc">${convFmt}</div>
          <div class="file-info">
            <div class="file-name" title="${convFilename}">${convFilename}</div>
            <div class="file-detail">${conversion.output_format || "—"}</div>
          </div>
        </div>
        <div class="status-row">
          ${statusBadge(conversion.status)}
          ${conversion.completed_at ? `<span class="ts-small">${fmtDate(conversion.completed_at)}</span>` : ""}
        </div>
        ${conversion.error_message ? `<div class="conv-error">${conversion.error_message}</div>` : ""}
        <div class="hover-hint">
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <circle cx="8" cy="8" r="6"/><path d="M8 6v4M8 11v.5"/>
          </svg>
          View details
        </div>
      </div>
    </div>

    <!-- FOOTER ACTIONS -->
    <div class="pair-footer">
      <span class="footer-ts">${fmtDate(upload.created_at)}</span>
      <div class="footer-actions">
        ${
          showDl
            ? `
        <button class="action-btn download"
                onclick="event.stopPropagation(); downloadFile('${conversion.result_cloudinary_url}','${convFilename}')">
          <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M8 2v9M4 11l4 4 4-4"/><path d="M2 14h12"/>
          </svg>
          Download
        </button>`
            : ""
        }
        <button class="action-btn delete"
                onclick="event.stopPropagation(); openModal('conversion','${conversion.id}')">
          <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M3 5h10M6 5V3h4v2M6 8v5M10 8v5M4 5l1 9h6l1-9"/>
          </svg>
          Delete conversion
        </button>
        <button class="action-btn delete"
                onclick="event.stopPropagation(); openModal('upload','${upload.id}')">
          <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
            <path d="M3 5h10M6 5V3h4v2M6 8v5M10 8v5M4 5l1 9h6l1-9"/>
          </svg>
          Delete upload
        </button>
      </div>
    </div>
  </div>`;
}

function renderList(rows) {
  const list = document.getElementById("fileList");
  if (!rows.length) {
    list.innerHTML = `<div class="empty">
      <div class="empty-icon">◌</div>
      <h3>No files yet</h3>
      <p>Upload a file to get started.</p>
      <a href="{{ url_for('Templates.index') }}" class="btn-upload" style="display:inline-flex">New upload</a>
    </div>`;
    return;
  }
  list.innerHTML = rows.map(renderCard).join("");
}

function applyFilter(filter) {
  activeFilter = filter;
  document
    .querySelectorAll(".tab")
    .forEach((t) => t.classList.toggle("active", t.dataset.filter === filter));
  let visible = allRows;
  if (filter !== "all") {
    visible = allRows.filter((c) => {
      const s = (c.status || "pending").toLowerCase();
      return s === filter || (filter === "done" && s === "completed");
    });
  }
  renderList(visible);
}


function renderPagination(current, total) {
  const pg = document.getElementById("pagination");
  if (total <= 1) {
    pg.innerHTML = "";
    return;
  }
  let html = "";
  for (let i = 1; i <= total; i++) {
    html += `<button class="pg-btn${i === current ? " active" : ""}" onclick="goPage(${i})">${i}</button>`;
  }
  pg.innerHTML = html;
}

async function goPage(page) {
  currentPage = page;
  await loadPage(page);
}

async function loadPage(page) {
  const data = await fetchConversions(page);
  if (!data) return;

  const conversions = Array.isArray(data)
    ? data
    : data.items || data.conversions || [];
  const total = data.total || conversions.length;
  const pages = data.pages || Math.ceil(total / perPage);

  document.getElementById("statUploads").textContent = total;
  document.getElementById("statPage").innerHTML =
    `${page} <span>/ ${pages}</span>`;
  document.getElementById("pageInfo").textContent =
    `${conversions.length} of ${total} items`;

  const doneCount = conversions.filter((c) => c.status === "completed").length;
  document.getElementById("statDone").textContent = doneCount;

  allRows = conversions;
  applyFilter(activeFilter);
  renderPagination(page, pages);
}

function viewUpload(uploadId) {
  window.location.href = `/uploaded/${uploadId}`;
}

function viewConversion(conversionId) {
  window.location.href = `/converted/${conversionId}`;
}

function openModal(type, id) {
  pendingDelete = { type, id };
  const label =
    type === "upload"
      ? "This will permanently remove the upload AND all its conversions."
      : "This will remove the converted file only. The original upload is kept.";
  document.getElementById("deleteWarning").textContent = label;
  document.getElementById("deleteModal").classList.add("open");
}

function closeModal() {
  pendingDelete = null;
  document.getElementById("deleteModal").classList.remove("open");
}

async function confirmDelete() {
  if (!pendingDelete) return;
  const { type, id } = pendingDelete;
  closeModal();

  const url =
    type === "upload"
      ? `/api/v1/uploaded/${id}/delete`
      : `/api/v1/converted/${id}/delete`;

  const res = await apiFetch(url, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
  });
  if (!res) return;
  if (!res.ok) {
    showToast("Delete failed", false);
    return;
  }
  showToast(type === "upload" ? "Upload deleted" : "Conversion deleted");
  loadPage(currentPage);
}

function downloadFile(url, name) {
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.target = "_blank";
  a.click();
}

async function handleLogout() {
  await apiFetch("/api/v1/auth/logout", { method: "POST" });
  window.location.href = "/";
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => applyFilter(tab.dataset.filter));
});

(async () => {
  loadUserFromStorage();
  const data = await fetchConversions(1);
  if (!data) return;

  const conversions = Array.isArray(data)
    ? data
    : data.items || data.conversions || [];

  const total = data.total || conversions.length;
  const pages = data.pages || Math.ceil(total / perPage);

  document.getElementById("statUploads").textContent = total;
  document.getElementById("statPage").innerHTML = `1 <span>/ ${pages}</span>`;
  document.getElementById("pageInfo").textContent =
    `${conversions.length} of ${total} items`;

  const doneCount = conversions.filter((c) => c.status === "completed").length;
  document.getElementById("statDone").textContent = doneCount;

  allRows = conversions;
  applyFilter(activeFilter);
  renderPagination(1, pages);
})();

window.viewUpload = viewUpload;
window.viewConversion = viewConversion;
window.openModal = openModal;
window.closeModal = closeModal;
window.confirmDelete = confirmDelete;
window.downloadFile = downloadFile;
window.handleLogout = handleLogout;
