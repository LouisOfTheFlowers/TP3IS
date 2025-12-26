/**
 * Admin Panel - Data Management Console
 * Controls the entire data pipeline
 */

const DATA_PROCESSOR_URL = "/data-processor";

// DOM Elements
const elements = {
  // Buttons
  btnScrape: document.getElementById("btn-scrape"),
  btnEnrich: document.getElementById("btn-enrich"),
  btnUpload: document.getElementById("btn-upload"),
  btnLoad: document.getElementById("btn-load"),
  btnRunAll: document.getElementById("btn-run-all"),
  btnCheckStatus: document.getElementById("btn-check-status"),
  btnClearLogs: document.getElementById("btn-clear-logs"),

  // Inputs
  recordCount: document.getElementById("record-count"),
  batchSize: document.getElementById("batch-size"),

  // Pipeline steps
  stepScrape: document.getElementById("step-scrape"),
  stepEnrich: document.getElementById("step-enrich"),
  stepUpload: document.getElementById("step-upload"),
  stepLoad: document.getElementById("step-load"),

  // Badges
  scrapeBadge: document.getElementById("scrape-badge"),
  enrichBadge: document.getElementById("enrich-badge"),
  uploadBadge: document.getElementById("upload-badge"),
  loadBadge: document.getElementById("load-badge"),

  // Outputs
  scrapeOutput: document.getElementById("scrape-output-content"),
  enrichOutput: document.getElementById("enrich-output-content"),
  uploadOutput: document.getElementById("upload-output-content"),
  loadOutput: document.getElementById("load-output-content"),

  // Stats
  scrapeStats: document.getElementById("scrape-stats"),
  enrichStats: document.getElementById("enrich-stats"),
  uploadStats: document.getElementById("upload-stats"),
  loadStats: document.getElementById("load-stats"),

  // Loading
  loadingOverlay: document.getElementById("loading-overlay"),
  loadingMessage: document.getElementById("loading-message"),

  // Error modal
  errorModal: document.getElementById("error-modal"),
  errorMessage: document.getElementById("error-message"),
  closeError: document.getElementById("close-error"),
};

// Application State
let state = {
  scrapeCompleted: false,
  enrichCompleted: false,
  uploadCompleted: false,
  loadCompleted: false,
  scrapeData: null,
  enrichData: null,
};

// ============================================================
// INITIALIZATION
// ============================================================

function init() {
  console.log("🔧 Initializing Data Management Console...");
  setupEventListeners();
  checkServiceHealth();
}

function setupEventListeners() {
  // Main action buttons
  elements.btnScrape?.addEventListener("click", handleScrape);
  elements.btnEnrich?.addEventListener("click", handleEnrich);
  elements.btnUpload?.addEventListener("click", handleUpload);
  elements.btnLoad?.addEventListener("click", handleLoad);

  // Quick actions
  elements.btnRunAll?.addEventListener("click", handleRunAll);
  elements.btnCheckStatus?.addEventListener("click", handleCheckStatus);
  elements.btnClearLogs?.addEventListener("click", handleClearLogs);

  // Clear buttons
  document.querySelectorAll(".clear-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.dataset.target;
      clearOutput(target + "-content");
    });
  });

  // Close error modal
  elements.closeError?.addEventListener("click", () => {
    elements.errorModal?.classList.add("hidden");
  });
}

async function checkServiceHealth() {
  try {
    addOutput(
      "scrape-output-content",
      "✓ Checking Data Processor service...",
      "info"
    );

    const response = await fetch(`${DATA_PROCESSOR_URL}/health`);
    if (response.ok) {
      const data = await response.json();
      addOutput(
        "scrape-output-content",
        `✓ Data Processor is healthy (${data.service})`,
        "success"
      );
    } else {
      throw new Error("Service unhealthy");
    }
  } catch (error) {
    addOutput(
      "scrape-output-content",
      `✗ Data Processor service unavailable. Some features may not work.`,
      "warning"
    );
  }
}

// ============================================================
// STEP 1: SCRAPE DATA
// ============================================================

async function handleScrape() {
  const recordCount = parseInt(elements.recordCount.value);

  if (!recordCount || recordCount < 100 || recordCount > 100000) {
    showError("Please enter a valid number of records (100-100,000)");
    return;
  }

  updatePipelineStep("scrape", "active");
  updateBadge("scrape", "running");
  elements.btnScrape.disabled = true;
  elements.scrapeStats.style.display = "grid";
  clearOutput("scrape-output-content");

  const startTime = Date.now();

  try {
    addOutput("scrape-output-content", `🚀 Starting data scraping...`, "info");
    addOutput(
      "scrape-output-content",
      `📊 Target: ${recordCount.toLocaleString()} records`,
      "info"
    );

    const response = await fetch(`${DATA_PROCESSOR_URL}/scrape`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit: recordCount }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Stream the response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop(); // Keep the last incomplete line

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            handleScrapeMessage(data);
          } catch (e) {
            addOutput("scrape-output-content", line, "info");
          }
        }
      }
    }

    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    document.getElementById("scrape-duration").textContent = `${duration}s`;

    addOutput(
      "scrape-output-content",
      `✅ Scraping completed successfully!`,
      "success"
    );

    state.scrapeCompleted = true;
    updatePipelineStep("scrape", "completed");
    updateBadge("scrape", "completed");
    elements.btnEnrich.disabled = false;
  } catch (error) {
    console.error("Scrape error:", error);
    addOutput("scrape-output-content", `❌ Error: ${error.message}`, "error");
    updatePipelineStep("scrape", "error");
    updateBadge("scrape", "error");
  } finally {
    elements.btnScrape.disabled = false;
  }
}

function handleScrapeMessage(data) {
  if (data.status === "progress") {
    addOutput(
      "scrape-output-content",
      `📥 Fetched ${data.records.toLocaleString()} records...`,
      "info"
    );
    document.getElementById("scrape-records").textContent =
      data.records.toLocaleString();
    document.getElementById("scrape-status").textContent = "Fetching...";
  } else if (data.status === "complete") {
    document.getElementById("scrape-records").textContent =
      data.total.toLocaleString();
    document.getElementById("scrape-status").textContent = "Completed";
    state.scrapeData = data;
  } else if (data.status === "error") {
    addOutput("scrape-output-content", `❌ ${data.message}`, "error");
  }
}

// ============================================================
// STEP 2: ENRICH WITH WEATHER
// ============================================================

async function handleEnrich() {
  if (!state.scrapeCompleted) {
    showError("Please complete Step 1 (Scrape Data) first");
    return;
  }

  updatePipelineStep("enrich", "active");
  updateBadge("enrich", "running");
  elements.btnEnrich.disabled = true;
  elements.enrichStats.style.display = "grid";
  clearOutput("enrich-output-content");

  try {
    addOutput(
      "enrich-output-content",
      `🌦️ Starting weather enrichment...`,
      "info"
    );

    const response = await fetch(`${DATA_PROCESSOR_URL}/enrich-weather`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Stream the response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            handleEnrichMessage(data);
          } catch (e) {
            addOutput("enrich-output-content", line, "info");
          }
        }
      }
    }

    addOutput(
      "enrich-output-content",
      `✅ Weather enrichment completed!`,
      "success"
    );

    state.enrichCompleted = true;
    updatePipelineStep("enrich", "completed");
    updateBadge("enrich", "completed");
    elements.btnUpload.disabled = false;
  } catch (error) {
    console.error("Enrich error:", error);
    addOutput("enrich-output-content", `❌ Error: ${error.message}`, "error");
    updatePipelineStep("enrich", "error");
    updateBadge("enrich", "error");
  } finally {
    elements.btnEnrich.disabled = false;
  }
}

function handleEnrichMessage(data) {
  if (data.status === "progress") {
    addOutput(
      "enrich-output-content",
      `🌡️ Processing date ${data.current}/${data.total}: ${data.date}`,
      "info"
    );
    document.getElementById("enrich-processed").textContent = data.current;
  } else if (data.status === "complete") {
    document.getElementById("enrich-processed").textContent =
      data.totalRecords.toLocaleString();
    document.getElementById("enrich-success").textContent =
      data.enrichedRecords.toLocaleString();
    document.getElementById("enrich-rate").textContent = `${data.successRate}%`;
    state.enrichData = data;
  } else if (data.status === "info") {
    addOutput("enrich-output-content", `ℹ️ ${data.message}`, "info");
  } else if (data.status === "error") {
    addOutput("enrich-output-content", `⚠️ ${data.message}`, "warning");
  }
}

// ============================================================
// STEP 3: UPLOAD TO SUPABASE
// ============================================================

async function handleUpload() {
  if (!state.enrichCompleted) {
    showError("Please complete Steps 1 & 2 first");
    return;
  }

  updatePipelineStep("upload", "active");
  updateBadge("upload", "running");
  elements.btnUpload.disabled = true;
  elements.uploadStats.style.display = "grid";
  clearOutput("upload-output-content");

  try {
    addOutput(
      "upload-output-content",
      `☁️ Starting upload to Supabase...`,
      "info"
    );

    const response = await fetch(`${DATA_PROCESSOR_URL}/upload-storage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    if (data.success) {
      addOutput(
        "upload-output-content",
        `✅ Uploaded: ${data.files.raw.name} (${data.files.raw.size})`,
        "success"
      );
      addOutput(
        "upload-output-content",
        `✅ Uploaded: ${data.files.weather.name} (${data.files.weather.size})`,
        "success"
      );

      document.getElementById("upload-files").textContent = "2";
      const totalSize = (
        parseFloat(data.files.raw.size) + parseFloat(data.files.weather.size)
      ).toFixed(2);
      document.getElementById("upload-size").textContent = `${totalSize} MB`;

      state.uploadCompleted = true;
      updatePipelineStep("upload", "completed");
      updateBadge("upload", "completed");
      elements.btnLoad.disabled = false;
    } else {
      throw new Error(data.error || "Upload failed");
    }
  } catch (error) {
    console.error("Upload error:", error);
    addOutput("upload-output-content", `❌ Error: ${error.message}`, "error");
    updatePipelineStep("upload", "error");
    updateBadge("upload", "error");
  } finally {
    elements.btnUpload.disabled = false;
  }
}

// ============================================================
// STEP 4: LOAD TO DATABASE
// ============================================================

async function handleLoad() {
  if (!state.uploadCompleted) {
    showError("Please complete Step 3 (Upload) first");
    return;
  }

  const batchSize = parseInt(elements.batchSize.value);

  if (!batchSize || batchSize < 10 || batchSize > 1000) {
    showError("Please enter a valid batch size (10-1000)");
    return;
  }

  updatePipelineStep("load", "active");
  updateBadge("load", "running");
  elements.btnLoad.disabled = true;
  elements.loadStats.style.display = "grid";
  clearOutput("load-output-content");

  try {
    addOutput("load-output-content", `💾 Starting database loading...`, "info");
    addOutput(
      "load-output-content",
      `📦 Batch size: ${batchSize} records`,
      "info"
    );

    const response = await fetch(`${DATA_PROCESSOR_URL}/load-database`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ batchSize }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // Stream the response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.trim()) {
          try {
            const data = JSON.parse(line);
            handleLoadMessage(data);
          } catch (e) {
            addOutput("load-output-content", line, "info");
          }
        }
      }
    }

    addOutput(
      "load-output-content",
      `✅ Database loading completed!`,
      "success"
    );

    state.loadCompleted = true;
    updatePipelineStep("load", "completed");
    updateBadge("load", "completed");
  } catch (error) {
    console.error("Load error:", error);
    addOutput("load-output-content", `❌ Error: ${error.message}`, "error");
    updatePipelineStep("load", "error");
    updateBadge("load", "error");
  } finally {
    elements.btnLoad.disabled = false;
  }
}

function handleLoadMessage(data) {
  if (data.status === "progress") {
    addOutput(
      "load-output-content",
      `📤 Batch ${data.batch}/${data.totalBatches}: ${data.message}`,
      "info"
    );
    document.getElementById("load-batches").textContent = data.batch;
    document.getElementById("load-records").textContent =
      data.recordsLoaded.toLocaleString();
  } else if (data.status === "complete") {
    document.getElementById("load-batches").textContent = data.totalBatches;
    document.getElementById("load-records").textContent =
      data.totalRecords.toLocaleString();
    document.getElementById("load-success-rate").textContent = data.successRate;
  } else if (data.status === "error") {
    addOutput("load-output-content", `❌ ${data.message}`, "error");
  }
}

// ============================================================
// QUICK ACTIONS
// ============================================================

async function handleRunAll() {
  if (
    !confirm(
      "This will run the entire pipeline. This may take several minutes. Continue?"
    )
  ) {
    return;
  }

  await handleScrape();
  if (state.scrapeCompleted) {
    await handleEnrich();
  }
  if (state.enrichCompleted) {
    await handleUpload();
  }
  if (state.uploadCompleted) {
    await handleLoad();
  }
}

async function handleCheckStatus() {
  addOutput("scrape-output-content", `🔍 Checking pipeline status...`, "info");

  const steps = [
    {
      name: "Scrape",
      completed: state.scrapeCompleted,
      output: "scrape-output-content",
    },
    {
      name: "Enrich",
      completed: state.enrichCompleted,
      output: "enrich-output-content",
    },
    {
      name: "Upload",
      completed: state.uploadCompleted,
      output: "upload-output-content",
    },
    {
      name: "Load",
      completed: state.loadCompleted,
      output: "load-output-content",
    },
  ];

  steps.forEach((step) => {
    const status = step.completed ? "✅ Completed" : "⏸️ Not completed";
    addOutput(step.output, `${step.name}: ${status}`, "info");
  });
}

function handleClearLogs() {
  clearOutput("scrape-output-content");
  clearOutput("enrich-output-content");
  clearOutput("upload-output-content");
  clearOutput("load-output-content");
  console.log("🧹 All logs cleared");
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function updatePipelineStep(step, status) {
  const stepElement = elements[`step${capitalize(step)}`];
  if (!stepElement) return;

  stepElement.classList.remove("active", "completed", "error");
  if (status !== "ready") {
    stepElement.classList.add(status);
  }

  const statusText = stepElement.querySelector(".step-status");
  if (statusText) {
    statusText.textContent = capitalize(status);
  }
}

function updateBadge(step, status) {
  const badge = elements[`${step}Badge`];
  if (!badge) return;

  badge.classList.remove("ready", "running", "completed", "error");
  badge.classList.add(status);
  badge.textContent = capitalize(status);
}

function addOutput(elementId, message, type = "info") {
  const output = document.getElementById(elementId);
  if (!output) return;

  // Remove placeholder if exists
  const placeholder = output.querySelector(".output-placeholder");
  if (placeholder) {
    placeholder.remove();
  }

  const line = document.createElement("div");
  line.className = `output-line ${type}`;
  line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
  output.appendChild(line);
  output.scrollTop = output.scrollHeight;
}

function clearOutput(elementId) {
  const output = document.getElementById(elementId);
  if (!output) return;

  output.innerHTML =
    '<p class="output-placeholder">Output cleared. Ready for new operations.</p>';
}

function showError(message) {
  elements.errorMessage.textContent = message;
  elements.errorModal?.classList.remove("hidden");
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ============================================================
// START APPLICATION
// ============================================================

document.addEventListener("DOMContentLoaded", init);
