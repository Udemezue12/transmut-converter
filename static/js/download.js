import { apiFetch } from "./fetchApi";
function getCookie(name) {
  const m = document.cookie.match(
    new RegExp(
      "(?:^|; )" + name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)",
    ),
  );
  return m ? decodeURIComponent(m[1]) : null;
}
function getExt(f) {
  return (f || "").split(".").pop().toUpperCase().slice(0, 6) || "FILE";
}
let conversionResults = [];

try {
  conversionResults = JSON.parse(
    sessionStorage.getItem("conversion_results") || "[]",
  );
} catch (e) {
  conversionResults = [];
}

// Extract task_id from URL: /download/<task_id>
const pathParts = window.location.pathname.split("/").filter(Boolean);
let taskId = pathParts[pathParts.length - 1];

if (!taskId || taskId === "download") {
  taskId = conversionResults.length ? conversionResults[0].task_id : null;
}

let pollInterval = null,
  pollCount = 0;
const MAX_POLLS = 72; 

function getTaskMeta(id) {
  return conversionResults.find((r) => r.task_id === id) || {};
}
const meta = getTaskMeta(taskId);
function renderProcessing() {
  document.getElementById("statusPanel").innerHTML = `
    <div class="ring-wrap">
      <svg class="ring-svg" viewBox="0 0 120 120">
        <circle class="ring-bg" cx="60" cy="60" r="54"/>
        <circle class="ring-fill processing" cx="60" cy="60" r="54"/>
      </svg>
      <div class="ring-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--accent2)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
        </svg>
      </div>
    </div>
    <div class="status-label processing">Processing</div>
    <div class="status-title">Converting your file<span class="dots"><span>.</span><span>.</span><span>.</span></span></div>
    <div class="status-sub">Your file is being converted. This usually takes just a few seconds — the page updates automatically.</div>
    <div class="task-card">
      <div class="task-row"><span class="task-key">task id</span><span class="task-val">${meta.filename || taskId}</span></div>
      <div class="task-row"><span class="task-key">status</span><span class="task-val" style="color:var(--accent2)">processing</span></div>
      <div class="task-row"><span class="task-key">checks</span><span class="task-val" id="pollCountDisplay">0</span></div>
    </div>
    <div class="eta" id="etaText">Checking status...</div>`;
}

function renderSuccess(data) {
  const meta = getTaskMeta(taskId);

  const filename = data.filename || meta.filename || "converted_file";
  const mime = data.mime || "";
  const downloadUrl = data.download_url || "#";
  const ext = getExt(filename);
  document.getElementById("statusPanel").innerHTML = `
    <div class="ring-wrap" style="opacity:0;animation:fadeUp 0.5s forwards">
      <svg class="ring-svg" viewBox="0 0 120 120">
        <circle class="ring-bg" cx="60" cy="60" r="54"/>
        <circle class="ring-fill" cx="60" cy="60" r="54" style="stroke-dashoffset:0"/>
      </svg>
      <div class="ring-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
      </div>
    </div>
    <div class="status-label success">Complete</div>
    <div class="status-title">Ready to download</div>
    <div class="status-sub">Your file has been converted successfully and is ready for download.</div>
    <div class="task-card">
      <div class="task-row"><span class="task-key">filename</span><span class="task-val">${filename}</span></div>
      <div class="task-row"><span class="task-key">format</span><span class="task-val" style="color:var(--success)">${ext}</span></div>
      ${mime ? `<div class="task-row"><span class="task-key">mime</span><span class="task-val">${mime}</span></div>` : ""}
      <div class="task-row"><span class="task-key">task id</span><span class="task-val">${taskId}</span></div>
    </div>
    <div class="actions">
      <a href="${downloadUrl}" class="btn btn-success" download="${filename}">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
        Download ${ext} file
      </a>
      <a href="/upload" class="btn btn-ghost">Convert another file</a>
    </div>`;
}

function renderError(msg, status) {
  document.getElementById("statusPanel").innerHTML = `
    <div class="ring-wrap">
      <svg class="ring-svg" viewBox="0 0 120 120">
        <circle class="ring-bg" cx="60" cy="60" r="54"/>
        <circle class="ring-fill error" cx="60" cy="60" r="54" style="stroke-dashoffset:110"/>
      </svg>
      <div class="ring-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </div>
    </div>
    <div class="status-label error">Failed</div>
    <div class="status-title">Conversion failed</div>
    <div class="status-sub">${msg || "Something went wrong. Please try again or contact support."}</div>
    <div class="task-card">
      <div class="task-row"><span class="task-key">status</span><span class="task-val" style="color:var(--danger)">${status || "error"}</span></div>
      <div class="task-row"><span class="task-key">task id</span><span class="task-val">${taskId}</span></div>
    </div>
    <div class="actions">
      <a href="/upload" class="btn btn-ghost" style="border-color:rgba(239,68,68,0.3);color:#fca5a5;">Try again</a>
    </div>`;
}

function renderOtherTasks() {
  const others = conversionResults.filter((t) => t.task_id !== taskId);

  if (!others.length) return;

  const el = document.getElementById("otherTasks");
  el.style.display = "block";

  el.innerHTML =
    `<h3>Other files in this batch</h3>` +
    others
      .map(
        (t) => `
      <div class="task-item" onclick="window.location.href='/api/v1/download/${t.task_id}'">
        <div class="task-item-icon">${getExt(t.filename)}</div>
        <div class="task-item-name">${t.filename || t.task_id}</div>
        <div class="task-item-status s-pending">PENDING</div>
      </div>
    `,
      )
      .join("");
}

async function pollStatus() {
  const res = await apiFetch(`/api/v1/download/${taskId}`, {
    redirect: "manual",
  });

  pollCount++;
  const countEl = document.getElementById("pollCountDisplay");
  if (countEl) countEl.textContent = pollCount;
  const etaEl = document.getElementById("etaText");

  if (!res) return; 
  if (res.type === "opaqueredirect" || res.status === 302 || res.status === 303) {
    clearInterval(pollInterval);
    const r2 = await apiFetch(`/api/v1/download/${taskId}`);
    if (!r2) return;
    if (r2.redirected) {
      renderSuccess({ filename: taskId, download_url: r2.url, mime: "" });
    } else {
      const data = await r2.json().catch(() => ({}));
      renderSuccess(data);
    }
    renderOtherTasks();
    return;
  }

  if (res.ok) {
    clearInterval(pollInterval);
    const data = await res.json();
    renderSuccess(data);
    renderOtherTasks();
    return;
  }

  if (res.status === 202) {
    const data = await res.json().catch(() => ({}));
    if (etaEl) etaEl.textContent = `Status: ${data.status || "processing"} — check #${pollCount}`;
    if (pollCount >= MAX_POLLS) {
      clearInterval(pollInterval);
      renderError("Conversion is taking longer than expected. Your file may still be processing — please check back later.", "timeout");
    }
    return;
  }

  if (res.status >= 400) {
    clearInterval(pollInterval);
    const err = await res.json().catch(() => ({}));
    renderError(err.error || "An error occurred during conversion.", err.status || String(res.status));
  }
}


if ((!taskId || taskId === "download") && conversionResults.length) {
  window.location.href = `/api/v1/download/${conversionResults[0].task_id}`;
} else if (!taskId || taskId === "download") {
  renderError(
    "No task ID found. Please start a new conversion.",
    "missing_task_id",
  );
} else {
  renderProcessing();
  renderOtherTasks();
  await pollStatus();
  pollInterval = setInterval(pollStatus, 2500);
}
