let selectedFiles = [];

const fileInput = document.getElementById("file-input");
const uploadZone = document.getElementById("upload-zone");
const previewWrap = document.getElementById("preview-wrap");
const runBtn = document.getElementById("run-btn");
const resultsContainer = document.getElementById("results-container");

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) load(e.target.files);
});

uploadZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadZone.classList.add("drag");
});
uploadZone.addEventListener("dragleave", () =>
  uploadZone.classList.remove("drag"),
);
uploadZone.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadZone.classList.remove("drag");
  if (e.dataTransfer.files.length > 0) load(e.dataTransfer.files);
});

function load(files) {
  selectedFiles = Array.from(files);
  previewWrap.innerHTML = ""; 
  previewWrap.style.display = "grid";
  
  selectedFiles.forEach(file => {
      const img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.className = "thumbnail-img";
      previewWrap.appendChild(img);
  });

  runBtn.disabled = false;
  hideError();
  resultsContainer.innerHTML = ""; 
}

function setStatus(msg) {
  const s = document.getElementById("status");
  s.classList.add("show");
  document.getElementById("status-text").textContent = msg;
}
function clearStatus() {
  document.getElementById("status").classList.remove("show");
}
function showError(msg) {
  const e = document.getElementById("error-box");
  e.textContent = msg;
  e.classList.add("show");
}
function hideError() {
  document.getElementById("error-box").classList.remove("show");
}

async function run() {
  if (selectedFiles.length === 0) return;
  hideError();
  runBtn.disabled = true;
  resultsContainer.innerHTML = "";

  const fd = new FormData();
  selectedFiles.forEach(file => {
      fd.append("image", file);
  });
  
  // NEW: Grab the selected model from the dropdown and append it
  const selectedModel = document.getElementById("model-select").value;
  fd.append("model", selectedModel);

  setStatus(`Processing ${selectedFiles.length} image(s)... This may take a moment due to API limits.`);
  try {
    const resp = await fetch("/api/analyze", {
      method: "POST",
      body: fd,
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Server error");

    clearStatus();
    renderResults(data.results);
  } catch (err) {
    clearStatus();
    showError(err.message);
  }
  runBtn.disabled = false;
}

function renderResults(resultsObj) {
    // CHANGED: Loop through the Dictionary (Object) instead of an Array
    Object.entries(resultsObj).forEach(([filename, data]) => {
        if (data.error) {
            const errHtml = `
                <div class="error-box show" style="margin-bottom: 2rem;">
                    <strong>${filename}:</strong> ${data.error}
                </div>
            `;
            resultsContainer.insertAdjacentHTML("beforeend", errHtml);
            return;
        }

        let chipsHtml = "";
        if (data.total === 0) {
            chipsHtml = '<span style="font-size:.85rem;color:var(--muted)">No findings detected</span>';
        } else {
            for (const [cls, cnt] of Object.entries(data.by_class)) {
                const isValidClass = ["cavity", "filling", "implant", "impacted"].includes(cls);
                const chipClass = isValidClass ? cls : "unknown";
                chipsHtml += `<span class="chip ${chipClass}">${cls} &times;${cnt}</span>`;
            }
        }

        const classCount = Object.keys(data.by_class).length;

        const resultHtml = `
            <div class="result-wrapper" style="margin-bottom: 3rem; padding-bottom: 1rem; border-bottom: 2px dashed var(--border);">
                <h2 style="font-size: 1.1rem; color: var(--accent); margin-bottom: 1rem;">File: ${filename}</h2>
                
                ${data.image_b64 ? `<img src="${data.image_b64}" class="annotated-img" alt="Annotated X-ray" />` : ''}

                <div class="card">
                    <div class="card-title">Detections</div>
                    <div class="stat-row">
                        <div class="stat">
                            <div class="val">${data.total}</div>
                            <div class="lbl">findings</div>
                        </div>
                        <div class="stat">
                            <div class="val">${classCount}</div>
                            <div class="lbl">classes</div>
                        </div>
                    </div>
                    <div class="chips">${chipsHtml}</div>
                </div>

                <div class="card">
                    <div class="card-title">Treatment Report</div>
                    <div class="role-badge">🩺 Clinical Chart Note</div>
                    <div class="report-content">${data.report}</div>
                </div>
            </div>
        `;

        resultsContainer.insertAdjacentHTML("beforeend", resultHtml);
    });
}