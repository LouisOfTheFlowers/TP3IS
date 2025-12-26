/**
 * NYC Collision Analytics Dashboard - Main Application
 */

import { apiService } from "./api.js";
import {
  createBarChart,
  createLineChart,
  createPieChart,
  createScatterChart,
  createHorizontalBarChart,
} from "./charts.js";

// DOM Elements
const elements = {
  loadingOverlay: document.getElementById("loading-overlay"),
  connectionStatus: document.getElementById("connection-status"),
  lastUpdate: document.getElementById("last-update"),
  errorModal: document.getElementById("error-modal"),
  errorMessage: document.getElementById("error-message"),
  closeError: document.getElementById("close-error"),
  loadDataBtn: document.getElementById("load-data-btn"),

  // Summary cards
  totalCollisions: document.getElementById("total-collisions"),
  totalInjured: document.getElementById("total-injured"),
  totalKilled: document.getElementById("total-killed"),
  totalDocuments: document.getElementById("total-documents"),

  // Tabs
  tabButtons: document.querySelectorAll(".tab-btn"),
  tabContents: document.querySelectorAll(".tab-content"),

  // Correlation tab
  highestRiskWeather: document.getElementById("highest-risk-weather"),
  highestRiskScore: document.getElementById("highest-risk-score"),
  mostAccidentsWeather: document.getElementById("most-accidents-weather"),
  highestFatalityWeather: document.getElementById("highest-fatality-weather"),
  correlationTable: document.getElementById("correlation-table"),

  // Weather tab
  weatherFilter: document.getElementById("weather-filter"),
  applyWeatherFilter: document.getElementById("apply-weather-filter"),
  clearWeatherFilter: document.getElementById("clear-weather-filter"),

  // Time tab
  timeGroupBy: document.getElementById("time-group-by"),
  timeStartDate: document.getElementById("time-start-date"),
  timeEndDate: document.getElementById("time-end-date"),
  applyTimeFilter: document.getElementById("apply-time-filter"),
  peakPeriod: document.getElementById("peak-period"),
  peakAccidents: document.getElementById("peak-accidents"),
  lowPeriod: document.getElementById("low-period"),
  lowAccidents: document.getElementById("low-accidents"),
  avgAccidents: document.getElementById("avg-accidents"),
};

// Application State
let state = {
  isConnected: false,
  dashboardData: null,
  weatherData: null,
  factorsData: null,
  timeData: null,
  correlationData: null,
};

// ============================================================
// INITIALIZATION
// ============================================================

async function init() {
  console.log("🚀 Initializing dashboard...");
  showLoading(true);

  try {
    // Setup event listeners
    setupEventListeners();

    // Check connection
    await checkConnection();

    // Load initial data
    await loadDashboardData();

    // Update status
    updateConnectionStatus(true);
  } catch (error) {
    console.error("Initialization error:", error);
    updateConnectionStatus(false);
    showError(
      "Failed to connect to the BI Service. Please ensure the services are running."
    );
  } finally {
    showLoading(false);
  }
}

// ============================================================
// EVENT LISTENERS
// ============================================================

function setupEventListeners() {
  // Tab navigation
  elements.tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Load data button
  elements.loadDataBtn?.addEventListener("click", handleLoadData);

  // Weather filter
  elements.applyWeatherFilter?.addEventListener("click", () => {
    loadWeatherData(elements.weatherFilter.value);
  });

  elements.clearWeatherFilter?.addEventListener("click", () => {
    elements.weatherFilter.value = "";
    loadWeatherData();
  });

  // Time filter
  elements.applyTimeFilter?.addEventListener("click", loadTimeData);
  elements.timeGroupBy?.addEventListener("change", loadTimeData);

  // Error modal
  elements.closeError?.addEventListener("click", () => {
    elements.errorModal.classList.add("hidden");
  });
}

// ============================================================
// DATA LOADING
// ============================================================

async function loadDashboardData() {
  try {
    // Load main dashboard data
    state.dashboardData = await apiService.getDashboard();

    // Update summary cards
    updateSummaryCards(state.dashboardData.summary);

    // Load correlation data (main feature)
    await loadCorrelationData();

    // Pre-load other tabs data
    loadWeatherData();
    loadFactorsData();
    loadTimeData();
  } catch (error) {
    console.error("Error loading dashboard:", error);
    throw error;
  }
}

async function loadCorrelationData() {
  try {
    state.correlationData = await apiService.getWeatherCorrelation();
    renderCorrelationTab(state.correlationData);
  } catch (error) {
    console.error("Error loading correlation data:", error);
  }
}

async function loadWeatherData(filter = null) {
  try {
    state.weatherData = await apiService.getCasualtiesByWeather(filter);
    renderWeatherTab(state.weatherData);
  } catch (error) {
    console.error("Error loading weather data:", error);
  }
}

async function loadFactorsData() {
  try {
    state.factorsData = await apiService.getContributingFactors(20);
    renderFactorsTab(state.factorsData);
  } catch (error) {
    console.error("Error loading factors data:", error);
  }
}

async function loadTimeData() {
  try {
    const startDate = elements.timeStartDate?.value || null;
    const endDate = elements.timeEndDate?.value || null;
    const groupBy = elements.timeGroupBy?.value || "hour";

    state.timeData = await apiService.getTimePeriod(
      startDate,
      endDate,
      groupBy
    );
    renderTimeTab(state.timeData);
  } catch (error) {
    console.error("Error loading time data:", error);
  }
}

// ============================================================
// RENDERING FUNCTIONS
// ============================================================

function updateSummaryCards(summary) {
  if (!summary) return;

  elements.totalCollisions.textContent = formatNumber(
    summary.totalCollisions || summary.total_collisions
  );
  elements.totalInjured.textContent = formatNumber(
    summary.totalInjured || summary.total_injured
  );
  elements.totalKilled.textContent = formatNumber(
    summary.totalKilled || summary.total_killed
  );
  elements.totalDocuments.textContent = formatNumber(
    summary.totalDocuments || summary.total_documents
  );
}

function renderCorrelationTab(data) {
  if (!data) return;

  // Update metrics
  const metrics = data.correlation_metrics;
  if (metrics) {
    elements.highestRiskWeather.textContent =
      metrics.highest_risk_weather || "--";
    elements.highestRiskScore.textContent = `Risk Score: ${
      metrics.highest_risk_score || "--"
    }`;
    elements.mostAccidentsWeather.textContent =
      metrics.most_accidents_weather || "--";
    elements.highestFatalityWeather.textContent =
      metrics.highest_fatality_weather || "--";
  }

  // Render charts
  const chartData = data.chart_ready;
  if (chartData) {
    // Bar chart
    createBarChart("correlation-bar-chart", chartData.bar_labels || [], [
      { label: "Accidents", data: chartData.bar_accidents || [] },
      { label: "Risk Score", data: chartData.bar_risk || [] },
    ]);

    // Scatter chart
    createScatterChart(
      "correlation-scatter-chart",
      chartData.scatter_data || [],
      {
        xLabel: "Total Accidents",
        yLabel: "Risk Score",
      }
    );
  }

  // Render table
  renderCorrelationTable(data.data);
}

function renderCorrelationTable(data) {
  if (!data || !elements.correlationTable) return;

  const tbody = elements.correlationTable.querySelector("tbody");
  tbody.innerHTML = "";

  data.forEach((item) => {
    const row = document.createElement("tr");
    row.innerHTML = `
            <td>${item.weather_condition}</td>
            <td>${formatNumber(item.total_accidents)}</td>
            <td>${formatNumber(item.total_injured)}</td>
            <td>${formatNumber(item.total_killed)}</td>
            <td>${item.fatality_rate?.toFixed(2) || "0.00"}</td>
            <td><strong>${item.risk_score?.toFixed(2) || "0.00"}</strong></td>
        `;
    tbody.appendChild(row);
  });
}

function renderWeatherTab(data) {
  if (!data) return;

  const chartData = data.chart_ready;
  if (chartData) {
    // Main bar chart
    createBarChart("weather-bar-chart", chartData.labels || [], [
      { label: "Injured", data: chartData.injured || [] },
      { label: "Killed", data: chartData.killed || [] },
    ]);

    // Severity chart
    createBarChart("weather-severity-chart", chartData.labels || [], [
      { label: "Severity Index", data: chartData.severity || [] },
    ]);

    // Pie chart
    createPieChart(
      "weather-pie-chart",
      chartData.labels?.slice(0, 8) || [],
      chartData.accidents?.slice(0, 8) || []
    );
  }
}

function renderFactorsTab(data) {
  if (!data) return;

  const chartData = data.chart_ready;
  if (chartData) {
    // Horizontal bar chart for factors
    createHorizontalBarChart("factors-bar-chart", chartData.labels || [], [
      { label: "Accident Count", data: chartData.values || [] },
    ]);

    // Pie chart
    createPieChart(
      "factors-pie-chart",
      chartData.labels || [],
      chartData.values || []
    );
  }

  // Category chart
  const categories = data.categorized;
  if (categories) {
    const categoryLabels = ["Driver Behavior", "External", "Vehicle", "Other"];
    const categoryValues = [
      categories.driver_behavior?.total_accidents || 0,
      categories.external?.total_accidents || 0,
      categories.vehicle?.total_accidents || 0,
      categories.other?.total_accidents || 0,
    ];

    createPieChart("factors-category-chart", categoryLabels, categoryValues, {
      doughnut: true,
    });
  }
}

function renderTimeTab(data) {
  if (!data) return;

  // Update insights
  const insights = data.insights;
  if (insights) {
    elements.peakPeriod.textContent = insights.peak_period || "--";
    elements.peakAccidents.textContent = `${formatNumber(
      insights.peak_accidents
    )} accidents`;
    elements.lowPeriod.textContent = insights.low_period || "--";
    elements.lowAccidents.textContent = `${formatNumber(
      insights.low_accidents
    )} accidents`;
    elements.avgAccidents.textContent =
      insights.average_accidents?.toFixed(1) || "--";
  }

  // Line chart
  const chartData = data.chart_ready;
  if (chartData) {
    createLineChart("time-line-chart", chartData.labels || [], [
      {
        label: "Accidents",
        data: chartData.accidents || [],
        fill: true,
        backgroundColor: "rgba(37, 99, 235, 0.1)",
      },
      { label: "Injured", data: chartData.injured || [] },
      { label: "Killed", data: chartData.killed || [] },
    ]);
  }
}

// ============================================================
// UI HELPERS
// ============================================================

function switchTab(tabId) {
  // Update buttons
  elements.tabButtons.forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabId);
  });

  // Update content
  elements.tabContents.forEach((content) => {
    content.classList.toggle("active", content.id === `${tabId}-tab`);
  });
}

function showLoading(show) {
  if (elements.loadingOverlay) {
    elements.loadingOverlay.classList.toggle("hidden", !show);
  }
}

function showError(message) {
  if (elements.errorModal && elements.errorMessage) {
    elements.errorMessage.textContent = message;
    elements.errorModal.classList.remove("hidden");
  }
}

function updateConnectionStatus(connected) {
  state.isConnected = connected;

  if (elements.connectionStatus) {
    elements.connectionStatus.textContent = connected
      ? "Connected"
      : "Disconnected";
    elements.connectionStatus.className = `status-badge ${
      connected ? "connected" : "disconnected"
    }`;
  }

  if (connected && elements.lastUpdate) {
    elements.lastUpdate.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
  }
}

async function checkConnection() {
  try {
    await apiService.healthCheck();
    return true;
  } catch (error) {
    return false;
  }
}

function formatNumber(num) {
  if (num === null || num === undefined) return "--";
  return new Intl.NumberFormat().format(num);
}

// ============================================================
// DATA LOADING HANDLER
// ============================================================

async function handleLoadData() {
  console.log("🔵 [Load Data] Button clicked");
  const btn = elements.loadDataBtn;
  const btnText = btn.querySelector(".btn-text");
  const originalText = btnText.textContent;

  try {
    // Disable button and show loading state
    btn.disabled = true;
    btn.classList.add("loading");
    btnText.textContent = "Loading...";
    console.log("🔵 [Load Data] Button disabled, making API call...");

    // Call the backend to load data (with duplicate checking)
    console.log("🔵 [Load Data] Sending POST to /api/load-data");
    const response = await fetch("/api/load-data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    console.log("🔵 [Load Data] Response received:", {
      status: response.status,
      statusText: response.statusText,
      ok: response.ok,
    });

    const result = await response.json();
    console.log("🔵 [Load Data] Response JSON:", result);

    if (result.success) {
      // Show success message
      console.log("✅ [Load Data] Success!", result.message);
      console.log("✅ [Load Data] Steps completed:", result.steps_completed);
      showSuccess(`✅ ${result.message}`);

      // Reload dashboard data
      console.log("🔵 [Load Data] Reloading dashboard data...");
      await loadDashboardData();
      console.log("✅ [Load Data] Dashboard data reloaded");

      // Update last update timestamp
      elements.lastUpdate.textContent = `Updated: ${new Date().toLocaleTimeString()}`;
    } else {
      console.error("❌ [Load Data] Failed:", result.message);
      console.error("❌ [Load Data] Error details:", result.error);
      showError(result.message || "Failed to load data");
    }
  } catch (error) {
    console.error("❌ [Load Data] Exception caught:", error);
    console.error("❌ [Load Data] Error stack:", error.stack);
    showError("Failed to load data. " + error.message);
  } finally {
    // Re-enable button
    btn.disabled = false;
    btn.classList.remove("loading");
    btnText.textContent = originalText;
    console.log("🔵 [Load Data] Button re-enabled");
  }
}

function showSuccess(message) {
  // Create a temporary success notification
  const notification = document.createElement("div");
  notification.className = "notification success";
  notification.textContent = message;
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--success-color);
    color: white;
    padding: 15px 25px;
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `;

  document.body.appendChild(notification);

  setTimeout(() => {
    notification.style.animation = "slideOut 0.3s ease";
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// ============================================================
// START APPLICATION
// ============================================================

document.addEventListener("DOMContentLoaded", init);
