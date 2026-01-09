// ==================== CONFIGURATION ====================
const API_BASE = "/api";
const REFRESH_INTERVAL = 120000; // 2 minutes (reduced from 30 seconds)
const CACHE_DURATION = 60000; // 1 minute cache

// ==================== STATE MANAGEMENT ====================
const state = {
  currentPage: "dashboard",
  isLoading: false,
  isConnected: false,
  charts: {},
  data: {},
  logs: [],
  cache: {}, // Add cache for API responses
  lastFetch: {}, // Track last fetch times
};

// ==================== UTILITY FUNCTIONS ====================
const utils = {
  // Show/hide loading overlay
  setLoading(isLoading, silent = false) {
    state.isLoading = isLoading;

    const loadingOverlay = document.getElementById("loading-overlay");
    const updateIndicator = document.getElementById("update-indicator");

    if (!silent) {
      // Show full loading overlay
      loadingOverlay.classList.toggle("active", isLoading);
      if (updateIndicator) {
        updateIndicator.style.display = "none";
      }
    } else {
      // Show subtle update indicator only
      if (updateIndicator) {
        updateIndicator.style.display = isLoading ? "inline-block" : "none";
      }
    }
  },

  // Show toast notification
  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = "slideIn 0.3s ease reverse";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  // API call wrapper with caching
  async apiCall(endpoint, options = {}) {
    const cacheKey = `${endpoint}_${JSON.stringify(options)}`;
    const now = Date.now();

    // Check if we have valid cached data
    if (
      state.cache[cacheKey] &&
      state.lastFetch[cacheKey] &&
      now - state.lastFetch[cacheKey] < CACHE_DURATION
    ) {
      console.log(`📦 Using cached data for ${endpoint}`);
      return state.cache[cacheKey];
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Cache the response
      state.cache[cacheKey] = data;
      state.lastFetch[cacheKey] = now;

      return data;
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);

      // Return cached data if available, even if expired
      if (state.cache[cacheKey]) {
        console.log(`⚠️ Using stale cached data for ${endpoint}`);
        return state.cache[cacheKey];
      }

      throw error;
    }
  },

  // Format numbers with commas
  formatNumber(num) {
    return num?.toLocaleString() || "0";
  },

  // Format date
  formatDate(date) {
    return new Date(date).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },

  // Add log entry
  addLog(message, type = "info") {
    const timestamp = new Date().toLocaleTimeString();
    state.logs.unshift({ message, type, timestamp });

    // Keep only last 50 logs
    if (state.logs.length > 50) {
      state.logs = state.logs.slice(0, 50);
    }

    this.updateLogs();
  },

  // Update logs display
  updateLogs() {
    const container = document.getElementById("operation-logs");
    if (!container) return;

    if (state.logs.length === 0) {
      container.innerHTML =
        '<p class="log-empty">No operations yet. Run a pipeline operation to see logs.</p>';
      return;
    }

    container.innerHTML = state.logs
      .map(
        (log) => `
      <div class="log-entry ${log.type}">
        <span>[${log.timestamp}]</span> ${log.message}
      </div>
    `
      )
      .join("");
  },

  // Clear API cache
  clearCache() {
    state.cache = {};
    state.lastFetch = {};
    console.log("🗑️ Cache cleared");
  },
};

// ==================== NAVIGATION ====================
const navigation = {
  init() {
    // Handle nav link clicks
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.addEventListener("click", (e) => {
        const page = e.currentTarget.dataset.page;
        this.navigateTo(page);
      });
    });

    // Handle browser back/forward
    window.addEventListener("popstate", (e) => {
      if (e.state && e.state.page) {
        this.navigateTo(e.state.page, false);
      }
    });

    // Set initial page from URL hash
    const hash = window.location.hash.slice(1);
    if (hash) {
      this.navigateTo(hash, false);
    }
  },

  navigateTo(page, pushState = true) {
    // Update active nav link
    document.querySelectorAll(".nav-link").forEach((link) => {
      link.classList.toggle("active", link.dataset.page === page);
    });

    // Show correct page
    document.querySelectorAll(".page-content").forEach((pageEl) => {
      pageEl.classList.toggle("active", pageEl.id === `page-${page}`);
    });

    state.currentPage = page;

    // Update URL
    if (pushState) {
      window.history.pushState({ page }, "", `#${page}`);
    }

    // Load page data
    this.loadPageData(page);
  },

  loadPageData(page) {
    switch (page) {
      case "dashboard":
        dashboard.load();
        break;
      case "xpath":
        xpathQueries.init();
        break;
      case "admin":
        admin.load();
        break;
    }
  },
};

// ==================== DASHBOARD PAGE ====================
const dashboard = {
  async load(forceRefresh = false) {
    try {
      // Use silent loading for auto-refreshes (no spinner)
      const isSilent = !forceRefresh && state.data.dashboard;
      utils.setLoading(true, isSilent);

      // Clear cache if forcing refresh
      if (forceRefresh) {
        state.cache = {};
        state.lastFetch = {};
      }

      // Load all data in parallel for better performance
      const [
        statsResponse,
        monthlyResponse,
        casualtiesResponse,
        collisionTypesResponse,
      ] = await Promise.all([
        utils.apiCall("/statistics"),
        utils.apiCall("/time-period?groupBy=month"),
        utils.apiCall("/weather-correlation"),
        utils.apiCall("/contributing-factors?limit=10"),
      ]);

      // Extract data
      const stats = statsResponse.data || statsResponse;
      const monthlyData = monthlyResponse.data || monthlyResponse;
      const casualtiesData = casualtiesResponse.data || casualtiesResponse;
      const collisionTypesData =
        collisionTypesResponse.data || collisionTypesResponse;

      state.data.dashboard = stats;

      // Update stats cards
      this.updateStats(stats);

      // Update charts without additional API calls
      this.createMonthlyChart(Array.isArray(monthlyData) ? monthlyData : []);
      this.createCasualtiesChart(
        Array.isArray(casualtiesData) ? casualtiesData : []
      );
      this.createCollisionTypesChart(
        Array.isArray(collisionTypesData) ? collisionTypesData : []
      );

      if (!isSilent) {
        utils.showToast("Dashboard data loaded successfully", "success");
      }
    } catch (error) {
      console.error("Dashboard load error:", error);
      utils.showToast("Failed to load dashboard data", "error");
    } finally {
      utils.setLoading(false);
    }
  },

  updateStats(stats) {
    document.getElementById("total-collisions").textContent =
      utils.formatNumber(stats.totalCollisions || 0);
    document.getElementById("total-fatalities").textContent =
      utils.formatNumber(stats.totalKilled || stats.totalFatalities || 0);
    document.getElementById("total-injuries").textContent = utils.formatNumber(
      stats.totalInjured || stats.totalInjuries || 0
    );
  },

  createMonthlyChart(data) {
    const ctx = document.getElementById("monthly-chart");
    if (!ctx) return;

    // Destroy existing chart
    if (state.charts.monthly) {
      state.charts.monthly.destroy();
      state.charts.monthly = null;
    }

    if (!data || data.length === 0) {
      ctx.style.display = "none";
      const container = ctx.parentElement;
      let msgDiv = container.querySelector(".no-data-message");
      if (!msgDiv) {
        msgDiv = document.createElement("div");
        msgDiv.className = "no-data-message";
        msgDiv.style.cssText =
          "padding: 2rem; text-align: center; color: var(--text-muted);";
        container.appendChild(msgDiv);
      }
      msgDiv.textContent = "No monthly data available";
      return;
    }

    ctx.style.display = "block";
    const msgDiv = ctx.parentElement.querySelector(".no-data-message");
    if (msgDiv) msgDiv.remove();

    state.charts.monthly = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.map((d) => d.period || d.month || "Unknown"),
        datasets: [
          {
            label: "Number of Collisions",
            data: data.map(
              (d) => parseInt(d.total_accidents || d.count || d.collisions) || 0
            ),
            backgroundColor: "rgba(37, 99, 235, 0.7)",
            borderColor: "rgba(37, 99, 235, 1)",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: "#cbd5e1" },
            grid: { color: "#334155" },
          },
          x: {
            ticks: { color: "#cbd5e1" },
            grid: { color: "#334155" },
          },
        },
      },
    });
  },

  createCasualtiesChart(data) {
    const ctx = document.getElementById("casualties-chart");
    if (!ctx) return;

    // Destroy existing chart
    if (state.charts.casualties) {
      state.charts.casualties.destroy();
      state.charts.casualties = null;
    }

    if (!data || data.length === 0) {
      ctx.style.display = "none";
      const container = ctx.parentElement;
      let msgDiv = container.querySelector(".no-data-message");
      if (!msgDiv) {
        msgDiv = document.createElement("div");
        msgDiv.className = "no-data-message";
        msgDiv.style.cssText =
          "padding: 2rem; text-align: center; color: var(--text-muted);";
        container.appendChild(msgDiv);
      }
      msgDiv.textContent = "No casualties data available";
      return;
    }

    ctx.style.display = "block";
    const msgDiv = ctx.parentElement.querySelector(".no-data-message");
    if (msgDiv) msgDiv.remove();

    state.charts.casualties = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.map(
          (d) => d.weather_condition || d.condition || d.weather || "Unknown"
        ),
        datasets: [
          {
            label: "Fatalities",
            data: data.map(
              (d) => parseInt(d.total_killed || d.fatalities) || 0
            ),
            backgroundColor: "rgba(239, 68, 68, 0.8)",
            borderColor: "rgba(239, 68, 68, 1)",
            borderWidth: 1,
          },
          {
            label: "Injuries",
            data: data.map((d) => parseInt(d.total_injured || d.injuries) || 0),
            backgroundColor: "rgba(245, 158, 11, 0.8)",
            borderColor: "rgba(245, 158, 11, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            labels: { color: "#cbd5e1" },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { color: "#cbd5e1" },
            grid: { color: "#334155" },
          },
          x: {
            ticks: { color: "#cbd5e1" },
            grid: { color: "#334155" },
          },
        },
      },
    });
  },

  createCollisionTypesChart(data) {
    const ctx = document.getElementById("collision-types-chart");
    if (!ctx) return;

    // Destroy existing chart
    if (state.charts.collisionTypes) {
      state.charts.collisionTypes.destroy();
      state.charts.collisionTypes = null;
    }

    if (!data || data.length === 0) {
      ctx.style.display = "none";
      const container = ctx.parentElement;
      let msgDiv = container.querySelector(".no-data-message");
      if (!msgDiv) {
        msgDiv = document.createElement("div");
        msgDiv.className = "no-data-message";
        msgDiv.style.cssText =
          "padding: 2rem; text-align: center; color: var(--text-muted);";
        container.appendChild(msgDiv);
      }
      msgDiv.textContent = "No collision type data available";
      return;
    }

    ctx.style.display = "block";
    const msgDiv = ctx.parentElement.querySelector(".no-data-message");
    if (msgDiv) msgDiv.remove();

    // Color palette for the pie chart
    const colors = [
      "rgba(37, 99, 235, 0.8)",
      "rgba(34, 197, 94, 0.8)",
      "rgba(245, 158, 11, 0.8)",
      "rgba(239, 68, 68, 0.8)",
      "rgba(139, 92, 246, 0.8)",
      "rgba(236, 72, 153, 0.8)",
      "rgba(6, 182, 212, 0.8)",
      "rgba(249, 115, 22, 0.8)",
      "rgba(132, 204, 22, 0.8)",
      "rgba(168, 162, 158, 0.8)",
    ];

    state.charts.collisionTypes = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.map(
          (d) => d.contributing_factor || d.factor || d.type || "Unknown"
        ),
        datasets: [
          {
            data: data.map(
              (d) => parseInt(d.accident_count || d.count || d.total) || 0
            ),
            backgroundColor: colors,
            borderColor: "#1e293b",
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: "right",
            labels: {
              color: "#cbd5e1",
              font: { size: 11 },
              padding: 10,
            },
          },
        },
      },
    });
  },

  createFactorsChart(data) {
    const ctx = document.getElementById("factors-chart");
    if (!ctx) return;

    // Destroy existing chart
    if (state.charts.factors) {
      state.charts.factors.destroy();
      state.charts.factors = null;
    }

    if (!data || data.length === 0) {
      ctx.style.display = "none";
      const container = ctx.parentElement;
      let msgDiv = container.querySelector(".no-data-message");
      if (!msgDiv) {
        msgDiv = document.createElement("div");
        msgDiv.className = "no-data-message";
        msgDiv.style.cssText =
          "padding: 2rem; text-align: center; color: var(--text-muted);";
        container.appendChild(msgDiv);
      }
      msgDiv.textContent = "No factors data available";
      return;
    }

    ctx.style.display = "block";
    const msgDiv = ctx.parentElement.querySelector(".no-data-message");
    if (msgDiv) msgDiv.remove();

    state.charts.factors = new Chart(ctx, {
      type: "horizontalBar",
      data: {
        labels: data.map(
          (d) =>
            d.contributing_factor ||
            d.factor ||
            d.contributingFactor ||
            "Unknown"
        ),
        datasets: [
          {
            label: "Occurrences",
            data: data.map((d) => parseInt(d.accident_count || d.count) || 0),
            backgroundColor: "rgba(16, 185, 129, 0.7)",
            borderColor: "rgba(16, 185, 129, 1)",
            borderWidth: 2,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false },
        },
        scales: {
          x: {
            beginAtZero: true,
            ticks: { color: "#cbd5e1" },
            grid: { color: "#334155" },
          },
          y: {
            ticks: { color: "#cbd5e1" },
            grid: { color: "#334155" },
          },
        },
      },
    });
  },

  createVehiclesChart(data) {
    const ctx = document.getElementById("vehicles-chart");
    if (!ctx) return;

    // Destroy existing chart
    if (state.charts.vehicles) {
      state.charts.vehicles.destroy();
      state.charts.vehicles = null;
    }

    if (!data || data.length === 0) {
      ctx.style.display = "none";
      const container = ctx.parentElement;
      let msgDiv = container.querySelector(".no-data-message");
      if (!msgDiv) {
        msgDiv = document.createElement("div");
        msgDiv.className = "no-data-message";
        msgDiv.style.cssText =
          "padding: 2rem; text-align: center; color: var(--text-muted);";
        container.appendChild(msgDiv);
      }
      msgDiv.textContent = "No vehicles data available";
      return;
    }

    ctx.style.display = "block";
    const msgDiv = ctx.parentElement.querySelector(".no-data-message");
    if (msgDiv) msgDiv.remove();

    state.charts.vehicles = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: data.map(
          (d) => d.vehicle_type || d.vehicleType || d.type || "Unknown"
        ),
        datasets: [
          {
            data: data.map(
              (d) => parseInt(d.involvement_count || d.count) || 0
            ),
            backgroundColor: [
              "rgba(37, 99, 235, 0.8)",
              "rgba(16, 185, 129, 0.8)",
              "rgba(245, 158, 11, 0.8)",
              "rgba(239, 68, 68, 0.8)",
              "rgba(139, 92, 246, 0.8)",
              "rgba(236, 72, 153, 0.8)",
              "rgba(14, 165, 233, 0.8)",
              "rgba(34, 197, 94, 0.8)",
              "rgba(251, 146, 60, 0.8)",
              "rgba(168, 85, 247, 0.8)",
            ],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: {
            position: "right",
            labels: { color: "#cbd5e1" },
          },
        },
      },
    });
  },
};

// ==================== XPATH QUERIES PAGE ====================
const xpathQueries = {
  queries: {
    1: "//col:collision[col:weather/col:condition='Rain' or col:weather/col:condition='Snow' or col:weather/col:condition='Fog']",
    2: "//col:collision[col:weather/col:condition[not(contains(., 'Rain')) and not(contains(., 'Snow')) and not(contains(., 'Fog'))]]",
    3: "//col:collision[count(col:vehicles/col:vehicle) >= 3]",
    4: "//col:collision[col:crashInfo/col:time[number(substring(., 1, 2)) >= 18 or number(substring(., 1, 2)) < 6]]",
    5: "//col:collision[col:casualties/col:personsKilled > 0]",
  },

  init() {
    // Set up event listeners
    document.querySelectorAll(".query-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const queryNum = e.currentTarget.dataset.query;
        this.runPredefinedQuery(queryNum);
      });
    });

    document
      .getElementById("execute-xpath")
      ?.addEventListener("click", () => this.runCustomQuery());
  },

  async runPredefinedQuery(queryNum) {
    const query = this.queries[queryNum];
    if (!query) return;

    document.getElementById("xpath-input").value = query;
    await this.executeQuery(query, 100);
  },

  async runCustomQuery() {
    const query = document.getElementById("xpath-input").value.trim();
    const limit = parseInt(document.getElementById("xpath-limit").value) || 100;

    if (!query) {
      utils.showToast("Please enter an XPath query", "warning");
      return;
    }

    await this.executeQuery(query, limit);
  },

  async executeQuery(query, limit) {
    try {
      utils.setLoading(true);

      const result = await utils.apiCall("/xpath", {
        method: "POST",
        body: JSON.stringify({ query, limit }),
      });

      this.displayResults(result);
      utils.showToast("Query executed successfully", "success");
    } catch (error) {
      console.error("XPath query error:", error);
      utils.showToast(`Query failed: ${error.message}`, "error");

      document.getElementById("xpath-output").innerHTML = `
        <div style="color: var(--error-color);">
          <strong>Error:</strong> ${error.message}
        </div>
      `;
    } finally {
      utils.setLoading(false);
    }
  },

  displayResults(result) {
    const statsContainer = document.getElementById("xpath-stats");
    const outputContainer = document.getElementById("xpath-output");

    if (!result.success || !result.data) {
      outputContainer.innerHTML =
        '<div style="color: var(--error-color);">No results returned</div>';
      return;
    }

    const results = result.data.results || [];
    const count = result.data.count || results.length;

    // Display stats
    statsContainer.innerHTML = `
      <div><strong>Results Found:</strong> ${utils.formatNumber(count)}</div>
      <div><strong>Displayed:</strong> ${utils.formatNumber(
        results.length
      )}</div>
      <div><strong>Execution Time:</strong> ${
        result.data.executionTime || "N/A"
      }</div>
    `;

    // Display results
    if (results.length === 0) {
      outputContainer.innerHTML =
        '<div style="color: var(--text-muted);">No matching collisions found</div>';
      return;
    }

    outputContainer.innerHTML = results
      .map(
        (collision, index) => `
      <div style="margin-bottom: 1rem; padding: 0.75rem; background: var(--surface-color); border-radius: 6px;">
        <strong>Result #${index + 1}</strong>
        <pre style="margin-top: 0.5rem; white-space: pre-wrap;">${JSON.stringify(
          collision,
          null,
          2
        )}</pre>
      </div>
    `
      )
      .join("");
  },
};

// ==================== ADMIN PAGE ====================
const admin = {
  async load() {
    utils.updateLogs();

    // Set up event listeners
    document
      .getElementById("run-pipeline")
      ?.addEventListener("click", () => this.runPipeline());
    document
      .getElementById("load-only")
      ?.addEventListener("click", () => this.loadDataOnly());
    document
      .getElementById("refresh-db-stats")
      ?.addEventListener("click", () => this.loadDbStats());
    document
      .getElementById("clear-logs")
      ?.addEventListener("click", () => this.clearLogs());
  },

  async runPipeline() {
    // Get the record limit from input
    const limitInput = document.getElementById("record-limit");
    const limit = limitInput ? parseInt(limitInput.value) || 100 : 100;

    if (
      !confirm(
        `This will run the full data pipeline:\n1. Scrape up to ${limit} new collision records\n2. Enrich with weather data\n3. Upload to storage bucket\n4. Load to database\n\nThis may take a few minutes. Continue?`
      )
    ) {
      return;
    }

    try {
      utils.setLoading(true);
      utils.addLog(
        `🚀 Starting full pipeline (limit: ${limit} records)...`,
        "info"
      );

      // Update UI status indicators
      this.updateStepStatus("scrape-status", "active", "Running...");
      this.updateStepStatus("enrich-status", "ready", "Pending");
      this.updateStepStatus("upload-status", "ready", "Pending");
      this.updateStepStatus("load-status", "ready", "Pending");

      utils.addLog(
        `📊 Step 1: Fetching up to ${limit} collision records from NYC Open Data...`,
        "info"
      );
      utils.showToast("Fetching collision data...", "info");

      // Call the load-data endpoint which runs the full pipeline
      const response = await fetch(`${API_BASE}/load-data`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ limit: limit }),
      });

      const result = await response.json();

      if (result.success) {
        // Update all steps to complete
        this.updateStepStatus("scrape-status", "success", "Complete");
        this.updateStepStatus("enrich-status", "success", "Complete");
        this.updateStepStatus("upload-status", "success", "Complete");
        this.updateStepStatus("load-status", "success", "Complete");

        utils.addLog("✅ Pipeline completed successfully!", "success");

        if (result.details && result.details.steps_completed) {
          result.details.steps_completed.forEach((step) => {
            utils.addLog(`   ✓ ${step}`, "success");
          });
        }

        utils.showToast(
          "Pipeline completed! Data loaded successfully.",
          "success"
        );

        // If we're on the dashboard, reload it
        if (state.currentPage === "dashboard") {
          await dashboard.load(true);
        }
      } else {
        throw new Error(result.message || "Pipeline failed");
      }
    } catch (error) {
      console.error("Pipeline error:", error);
      utils.addLog(`❌ Pipeline failed: ${error.message}`, "error");
      utils.showToast(`Pipeline failed: ${error.message}`, "error");

      // Mark failed step
      this.updateStepStatus("scrape-status", "error", "Failed");
    } finally {
      utils.setLoading(false);
    }
  },

  async loadDataOnly() {
    try {
      utils.setLoading(true);
      utils.addLog("Starting data load to database...", "info");
      this.updateStepStatus("load-status", "active", "Loading...");

      const result = await utils.apiCall("/load-data", {
        method: "POST",
      });

      utils.addLog("Data loaded successfully", "success");
      this.updateStepStatus("load-status", "success", "Complete");
      utils.showToast("Data loaded successfully", "success");
    } catch (error) {
      console.error("Load data error:", error);
      utils.addLog(`Load failed: ${error.message}`, "error");
      this.updateStepStatus("load-status", "error", "Failed");
      utils.showToast("Failed to load data", "error");
    } finally {
      utils.setLoading(false);
    }
  },

  updateStepStatus(elementId, status, text) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = text;
    element.parentElement.className = `step ${status}`;
  },

  clearLogs() {
    state.logs = [];
    utils.updateLogs();
    utils.showToast("Logs cleared", "info");
  },
};

// ==================== CONNECTION MONITORING ====================
const connectionMonitor = {
  async checkConnection() {
    try {
      // Use a simple fetch without going through apiCall to avoid caching
      const response = await fetch(`${API_BASE}/health`, {
        method: "GET",
        cache: "no-cache",
      });
      this.setStatus(response.ok);
    } catch (error) {
      this.setStatus(false);
    }
  },

  setStatus(isConnected) {
    state.isConnected = isConnected;
    const statusBadge = document.getElementById("connection-status");
    const statusText = document.getElementById("status-text");

    if (isConnected) {
      statusBadge.className = "status-badge connected";
      statusText.textContent = "Connected";
    } else {
      statusBadge.className = "status-badge error";
      statusText.textContent = "Disconnected";
    }
  },

  start() {
    this.checkConnection();
    setInterval(() => this.checkConnection(), 10000); // Check every 10 seconds
  },
};

// ==================== INITIALIZATION ====================
document.addEventListener("DOMContentLoaded", () => {
  console.log("🚀 NYC Collision Analytics - Initializing...");

  // Initialize navigation
  navigation.init();

  // Set up refresh button
  document
    .getElementById("refresh-dashboard")
    ?.addEventListener("click", () => {
      if (state.currentPage === "dashboard") {
        dashboard.load(true); // Force refresh with spinner
      }
    });

  // Start connection monitoring
  connectionMonitor.start();

  // Auto-refresh dashboard data (silent, no spinner)
  setInterval(() => {
    if (state.currentPage === "dashboard" && !state.isLoading) {
      dashboard.load(false); // Silent refresh without spinner
    }
  }, REFRESH_INTERVAL);

  console.log("✅ Application ready");
});
