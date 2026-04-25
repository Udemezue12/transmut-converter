import { apiFetch } from "./apifetch.js";
import { hasAccessToken } from "./cookies.js";

export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
export async function startConversions(detectedData, selectedFormats) {
  const promises = detectedData.map(async (file, i) => {
    if ((file.allowed_formats || []).length === 0) return null;

    if (!selectedFormats[i]) return null; // 🔥 important safety

    const resp = await apiFetch("/api/v1/start/conversion", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        temp_file_id: file.temp_file_id,
        mime: file.mime,
        file_type: file.file_type,
        output_format: selectedFormats[i],
        filename: file.filename,
      }),
    });

    let data;

    try {
      data = await resp.json();
    } catch (e) {
      const text = await resp.text();
      console.error("Non-JSON response:", text);
      throw new Error("Server returned invalid response");
    }

    return {
      task_id: data.task_id,
      originalName: file.filename,
    };
  });

  const results = await Promise.all(promises);
  return results.filter(Boolean);
}
export async function pollTask(task) {
  const { task_id, originalName } = task;

  while (true) {
    await delay(1500); // polling interval

    const resp = await apiFetch(`/api/v1/result/${task_id}`);
    let data;

    try {
      data = await resp.json();
    } catch (e) {
      const text = await resp.text();
      console.error("Non-JSON response:", text);
      throw new Error("Server returned invalid response");
    }
    // 🔥 Optional: update UI per file
    console.log(`Task ${originalName}:`, data.status);

    if (data.status == "COMPLETED") {
      return {
        filename: data.filename,
        download_url: data.download_url,
      };
    }

    if (data.status == "FAILED") {
      throw new Error(data.error || `Failed: ${originalName}`);
    }
  }
}
export async function waitForAllTasks(tasks) {
  const pollingPromises = tasks.map((task) => pollTask(task));
  return Promise.all(pollingPromises);
}
export async function downloadFile(file, showToast) {
  try {
   
    const resp = await apiFetch(
      `/api/v1/media/converted/${encodeURIComponent(file.filename)}`,
    );

    if (!resp.ok) throw new Error("Download failed");

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = file.filename;
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
  } catch (err) {
    console.error("Download error:", err);
    showToast(`Failed to download ${file.filename}`, "error");
  }
}
export async function downloadQueue(files, showToast) {
  for (let i = 0; i < files.length; i++) {
    const file = files[i];

    showToast(`Downloading ${file.filename}...`, "info");

    await downloadFile(file, showToast);

    await delay(1200);
  }
}
export function handleRedirectAfterDownload() {
  const overlay = document.getElementById("loaderOverlay");

  const waitTime = hasAccessToken() ? 12000 : 3000;

  document.getElementById("loaderText").textContent = "Finalizing...";
  document.getElementById("loaderSub").textContent = hasAccessToken()
    ? "Preparing your downloads..."
    : "Wrapping up...";

  setTimeout(() => {
    overlay.classList.remove("show");
    window.location.href = window.APP_CONFIG.homeUrl;
  }, waitTime);
}
