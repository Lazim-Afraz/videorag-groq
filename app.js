const API = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000/api"
  : "/api";

// ── State ────────────────────────────────────────────────
let sessionId = null;
let selectedFile = null;

// ── DOM refs ─────────────────────────────────────────────
const dropZone      = document.getElementById("dropZone");
const fileInput     = document.getElementById("fileInput");
const browseBtn     = document.getElementById("browseBtn");
const fileInfo      = document.getElementById("fileInfo");
const fileName      = document.getElementById("fileName");
const clearFile     = document.getElementById("clearFile");
const processBtn    = document.getElementById("processBtn");
const progressWrap  = document.getElementById("progressWrap");
const progressFill  = document.getElementById("progressFill");
const progressLabel = document.getElementById("progressLabel");
const sessionInfo   = document.getElementById("sessionInfo");
const sessionFilename = document.getElementById("sessionFilename");
const sessionSegments = document.getElementById("sessionSegments");
const emptyState    = document.getElementById("emptyState");
const chatFeed      = document.getElementById("chatFeed");
const queryInput    = document.getElementById("queryInput");
const evalToggle    = document.getElementById("evalToggle");
const sendBtn       = document.getElementById("sendBtn");

// ── File selection ────────────────────────────────────────
browseBtn.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", e => {
  e.preventDefault();
  dropZone.classList.add("over");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("over");
  const f = e.dataTransfer.files[0];
  if (f) setFile(f);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});

function setFile(f) {
  selectedFile = f;
  fileName.textContent = f.name;
  fileInfo.classList.remove("hidden");
  processBtn.disabled = false;
}

clearFile.addEventListener("click", () => {
  selectedFile = null;
  fileInput.value = "";
  fileInfo.classList.add("hidden");
  processBtn.disabled = true;
});

// ── Upload + process ──────────────────────────────────────
processBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  processBtn.disabled = true;
  showProgress("Uploading…", 15);

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    showProgress("Transcribing with Whisper…", 40);

    const res = await fetch(`${API}/upload`, { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Processing failed.");
    }

    showProgress("Building search index…", 80);
    await sleep(400); // let the bar visually reach 80

    showProgress("Done.", 100);
    await sleep(350);

    sessionId = data.session_id;
    activateSession(data.segment_count);
  } catch (err) {
    hideProgress();
    processBtn.disabled = false;
    alert("Error: " + err.message);
  }
});

function showProgress(label, pct) {
  progressWrap.classList.remove("hidden");
  progressFill.style.width = pct + "%";
  progressLabel.textContent = label;
}

function hideProgress() {
  progressWrap.classList.add("hidden");
  progressFill.style.width = "0%";
}

function activateSession(segCount) {
  hideProgress();
  sessionFilename.textContent = selectedFile.name;
  sessionSegments.textContent = `${segCount} segments indexed`;
  sessionInfo.hidden = false;

  // Enable query UI
  emptyState.classList.add("hidden");
  chatFeed.hidden = false;
  queryInput.disabled = false;
  sendBtn.disabled = false;
  queryInput.focus();
}

// ── Query ─────────────────────────────────────────────────
sendBtn.addEventListener("click", submitQuery);
queryInput.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) submitQuery();
});

async function submitQuery() {
  const q = queryInput.value.trim();
  if (!q || !sessionId) return;

  queryInput.value = "";
  sendBtn.disabled = true;
  queryInput.disabled = true;

  appendUserBubble(q);
  const thinkingEl = appendThinking();

  try {
    const res = await fetch(`${API}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        question: q,
        top_k: 5,
        evaluate: evalToggle.checked,
      }),
    });
    const data = await res.json();

    thinkingEl.remove();

    if (!res.ok) {
      appendErrorBubble(data.detail || "Something went wrong.");
    } else {
      appendAnswerBubble(data);
    }
  } catch (err) {
    thinkingEl.remove();
    appendErrorBubble("Network error: " + err.message);
  } finally {
    sendBtn.disabled = false;
    queryInput.disabled = false;
    queryInput.focus();
  }
}

// ── Chat rendering ────────────────────────────────────────
function appendUserBubble(text) {
  const msg = el("div", "msg msg-user");
  msg.innerHTML = `<span class="bubble-user">${esc(text)}</span>`;
  chatFeed.appendChild(msg);
  scroll();
}

function appendThinking() {
  const msg = el("div", "msg msg-assistant thinking");
  msg.innerHTML = `<span>Thinking</span> <div class="dot-pulse"><span></span><span></span><span></span></div>`;
  chatFeed.appendChild(msg);
  scroll();
  return msg;
}

function appendAnswerBubble(data) {
  const showEn = data.detected_language !== "en" && data.answer_en;

  const segmentsHtml = data.segments.map(s => `
    <div class="segment">
      <span class="seg-ts">${esc(s.timestamp)}</span>${esc(s.text)}
    </div>
  `).join("");

  const evalHtml = buildEvalHtml(data.evaluation);

  const enHtml = showEn ? `
    <div class="answer-en">
      <strong>English:</strong> ${esc(data.answer_en)}
    </div>
  ` : "";

  const msg = el("div", "msg msg-assistant");
  msg.innerHTML = `
    <div class="bubble-assistant">
      <div class="answer-text">${esc(data.answer)}</div>
      ${enHtml}
      <button class="segments-toggle" data-open="false">
        Show ${data.segments.length} source segments ▾
      </button>
      <div class="segments-list" style="display:none">${segmentsHtml}</div>
      ${evalHtml}
    </div>
  `;

  msg.querySelector(".segments-toggle").addEventListener("click", function () {
    const list = this.nextElementSibling;
    const open = this.dataset.open === "true";
    list.style.display = open ? "none" : "flex";
    this.dataset.open = !open;
    this.textContent = open
      ? `Show ${data.segments.length} source segments ▾`
      : `Hide source segments ▴`;
  });

  chatFeed.appendChild(msg);
  scroll();
}

function buildEvalHtml(ev) {
  if (!ev || Object.keys(ev).length === 0) return "";
  const scoreKeys = ["Relevance", "Accuracy", "Fluency", "Overall"];
  const chips = scoreKeys
    .filter(k => ev[k] !== undefined)
    .map(k => `<span class="score-chip">${k} ${ev[k]}/10</span>`)
    .join("");
  const comment = ev.Comments ? `<p class="eval-comment">${esc(ev.Comments)}</p>` : "";
  return `<div class="eval-row">${chips}</div>${comment}`;
}

function appendErrorBubble(msg) {
  const el_ = el("div", "msg msg-assistant");
  el_.innerHTML = `<div class="bubble-assistant" style="border-color:var(--red);color:#f87171;">${esc(msg)}</div>`;
  chatFeed.appendChild(el_);
  scroll();
}

// ── Helpers ───────────────────────────────────────────────
function el(tag, cls) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  return e;
}

function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function scroll() {
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}
