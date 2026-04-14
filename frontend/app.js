const els = {
  backendUrl: document.getElementById("backendUrl"),
  task: document.getElementById("task"),
  message: document.getElementById("message"),
  filePath: document.getElementById("filePath"),
  relativeFilePath: document.getElementById("relativeFilePath"),
  code: document.getElementById("code"),
  language: document.getElementById("language"),
  autonomousMode: document.getElementById("autonomousMode"),
  runValidation: document.getElementById("runValidation"),
  generateTests: document.getElementById("generateTests"),
  intelligenceLevel: document.getElementById("intelligenceLevel"),
  sendBtn: document.getElementById("sendBtn"),
  clearBtn: document.getElementById("clearBtn"),
  status: document.querySelector(".status"),
  statusText: document.getElementById("statusText"),
  response: document.getElementById("response"),
  updatedFiles: document.getElementById("updatedFiles"),
};

const STORAGE_KEY = "agent-control-room";

function setStatus(text, mode = "idle") {
  els.status.classList.remove("ok", "err");
  if (mode === "ok") els.status.classList.add("ok");
  if (mode === "err") els.status.classList.add("err");
  els.statusText.textContent = text;
}

function saveSettings() {
  const data = {
    backendUrl: els.backendUrl.value.trim(),
    task: els.task.value,
    filePath: els.filePath.value.trim(),
    relativeFilePath: els.relativeFilePath.value.trim(),
    language: els.language.value.trim(),
    autonomousMode: els.autonomousMode.checked,
    runValidation: els.runValidation.checked,
    generateTests: els.generateTests.checked,
    intelligenceLevel: els.intelligenceLevel.value,
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}

function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    if (data.backendUrl) els.backendUrl.value = data.backendUrl;
    if (data.task) els.task.value = data.task;
    if (data.filePath) els.filePath.value = data.filePath;
    if (data.relativeFilePath) els.relativeFilePath.value = data.relativeFilePath;
    if (data.language) els.language.value = data.language;
    if (typeof data.autonomousMode === "boolean") els.autonomousMode.checked = data.autonomousMode;
    if (typeof data.runValidation === "boolean") els.runValidation.checked = data.runValidation;
    if (typeof data.generateTests === "boolean") els.generateTests.checked = data.generateTests;
    if (data.intelligenceLevel) els.intelligenceLevel.value = data.intelligenceLevel;
  } catch {
    // Ignore malformed localStorage entries.
  }
}

function buildPayload() {
  return {
    task: els.task.value,
    message: els.message.value.trim(),
    filePath: els.filePath.value.trim() || undefined,
    relativeFilePath: els.relativeFilePath.value.trim() || undefined,
    language: els.language.value.trim() || undefined,
    code: els.code.value || undefined,
    runValidation: els.runValidation.checked,
    generateTests: els.generateTests.checked,
    autonomousMode: els.autonomousMode.checked,
    intelligenceLevel: els.intelligenceLevel.value,
  };
}

function renderUpdatedFiles(files) {
  if (!Array.isArray(files) || files.length === 0) {
    els.updatedFiles.innerHTML = '<p class="hint">No changed files returned by backend.</p>';
    return;
  }

  els.updatedFiles.innerHTML = "";
  files.forEach((item, index) => {
    const card = document.createElement("article");
    card.className = "file-card";

    const button = document.createElement("button");
    button.className = "file-head";
    button.type = "button";
    button.textContent = item.path || `updated-file-${index + 1}`;

    const content = document.createElement("div");
    content.className = "file-content";

    const pre = document.createElement("pre");
    pre.textContent = typeof item.content === "string" ? item.content : "";
    content.appendChild(pre);

    button.addEventListener("click", () => {
      content.classList.toggle("open");
    });

    card.appendChild(button);
    card.appendChild(content);
    els.updatedFiles.appendChild(card);
  });
}

async function callAgent() {
  const payload = buildPayload();
  if (!payload.message) {
    setStatus("Enter a prompt first.", "err");
    return;
  }

  saveSettings();
  els.sendBtn.disabled = true;
  setStatus("Agent is thinking and executing...", "idle");

  try {
    const url = `${els.backendUrl.value.trim().replace(/\/$/, "")}/chat`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`HTTP ${response.status}: ${body}`);
    }

    const result = await response.json();
    els.response.textContent = result.response || "(empty response)";
    renderUpdatedFiles(result.updatedFiles);
    setStatus("Completed successfully.", "ok");
  } catch (error) {
    const text = error instanceof Error ? error.message : String(error);
    els.response.textContent = text;
    setStatus("Request failed.", "err");
  } finally {
    els.sendBtn.disabled = false;
  }
}

function clearOutput() {
  els.response.textContent = "No response yet.";
  els.updatedFiles.innerHTML = '<p class="hint">No changed files yet.</p>';
  setStatus("Idle");
}

els.sendBtn.addEventListener("click", callAgent);
els.clearBtn.addEventListener("click", clearOutput);

[
  els.backendUrl,
  els.task,
  els.filePath,
  els.relativeFilePath,
  els.language,
  els.autonomousMode,
  els.runValidation,
  els.generateTests,
  els.intelligenceLevel,
].forEach((node) => {
  node.addEventListener("change", saveSettings);
});

loadSettings();
