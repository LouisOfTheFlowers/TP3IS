/**
 * NYC Collision Analytics Dashboard - Main Application
 */

import { apiService } from "./api.js";
import { xpathQueryService } from "./xpath-queries.js";
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

  // XPath tab
  xpathQueryButtons: document.querySelectorAll(".xpath-query-btn"),
  xpathResults: document.getElementById("xpath-results"),
  xpathNoResults: document.getElementById("xpath-no-results"),
  xpathQueryTitle: document.getElementById("xpath-query-title"),
  xpathQueryDescription: document.getElementById("xpath-query-description"),
  xpathExpression: document.getElementById("xpath-expression"),
  xpathTotalResults: document.getElementById("xpath-total-results"),
  xpathMetric1: document.getElementById("xpath-metric-1"),
  xpathLabel1: document.getElementById("xpath-label-1"),
  xpathMetric2: document.getElementById("xpath-metric-2"),
  xpathLabel2: document.getElementById("xpath-label-2"),
  xpathTableHead: document.getElementById("xpath-table-head"),
  xpathTableBody: document.getElementById("xpath-table-body"),
  xpathChart1: document.getElementById("xpath-chart-1"),
  xpathChart2: document.getElementById("xpath-chart-2"),
  xpathChart1Title: document.getElementById("xpath-chart-1-title"),
  xpathChart2Title: document.getElementById("xpath-chart-2-title"),
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

  // XPath query buttons
  elements.xpathQueryButtons?.forEach((btn) => {
    btn.addEventListener("click", () => handleXPathQuery(btn.dataset.query));
  });
}

// ============================================================
// DATA LOADING
// ============================================================

async function loadDashboardData() {
  try {
    // Step 1: Load quick cached data first (instant)
    console.log("📊 Loading cached dashboard data...");
    const cachedData = await apiService.getDashboard(true);

    if (cachedData.success) {
      // Update with cached data immediately
      state.dashboardData = cachedData;
      updateSummaryCards(cachedData.data || cachedData.summary);
      console.log("✅ Cached data loaded");
    }

    // Step 2: Load full data in background
    console.log("🔄 Loading full dashboard data...");
    state.dashboardData = await apiService.getDashboard(false);

    // Update with real data
    updateSummaryCards(state.dashboardData.data || state.dashboardData.summary);
    console.log("✅ Full data loaded");

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
// XPATH QUERIES
// ============================================================

let xpathCharts = { chart1: null, chart2: null };

async function handleXPathQuery(queryType) {
  showLoading(true);
  elements.xpathNoResults?.classList.add("hidden");
  elements.xpathResults?.classList.add("hidden");

  try {
    let results, queryInfo;

    switch (queryType) {
      case "highRisk":
        results = await xpathQueryService.getHighRiskAccidents();
        queryInfo = {
          title: "Query 1: High-Risk Accidents in Adverse Weather",
          description:
            "Accidents with 3+ injuries OR any fatalities during Rain/Snow conditions",
          xpath: `//collision[weather/condition[contains(text(), 'Rain') or contains(text(), 'Snow')] and (casualties/personsInjured >= 3 or casualties/personsKilled > 0)]`,
        };
        renderHighRiskResults(results, queryInfo);
        break;

      case "vulnerable":
        results = await xpathQueryService.getVulnerableUsersInAdverseWeather();
        queryInfo = {
          title: "Query 2: Vulnerable Road Users in Adverse Weather",
          description:
            "Pedestrians and cyclists injured/killed during non-Clear weather conditions",
          xpath: `//collision[weather/condition[not(contains(text(), 'Clear'))] and (casualties/pedestriansInjured > 0 or casualties/pedestriansKilled > 0 or casualties/cyclistsInjured > 0 or casualties/cyclistsKilled > 0)]`,
        };
        renderVulnerableUsersResults(results, queryInfo);
        break;

      case "multiVehicle":
        results = await xpathQueryService.getMultiVehicleFactorAnalysis();
        queryInfo = {
          title: "Query 3: Multi-Vehicle Accidents with Key Factors",
          description:
            "Accidents involving 3+ vehicles with Distraction, Speed, or Following Too Closely factors",
          xpath: `//collision[count(vehicles/vehicle[text() != '']) >= 3 and contributingFactors/factor[contains(text(), 'Distraction') or contains(text(), 'Speed') or contains(text(), 'Following')]]`,
        };
        renderMultiVehicleResults(results, queryInfo);
        break;

      default:
        throw new Error("Unknown query type");
    }

    elements.xpathResults?.classList.remove("hidden");
  } catch (error) {
    console.error("XPath query error:", error);
    showError(`Failed to execute XPath query: ${error.message}`);
  } finally {
    showLoading(false);
  }
}

function renderHighRiskResults(results, queryInfo) {
  // Update header
  elements.xpathQueryTitle.textContent = queryInfo.title;
  elements.xpathQueryDescription.textContent = queryInfo.description;
  elements.xpathExpression.textContent = queryInfo.xpath;

  // Update summary cards
  elements.xpathTotalResults.textContent =
    results.totalHighRiskAccidents.toLocaleString();
  document.getElementById("xpath-total-label").textContent =
    "High-Risk Accidents";

  const totalInjured = Object.values(results.weatherBreakdown).reduce(
    (sum, w) => sum + w.totalInjured,
    0
  );
  const totalKilled = Object.values(results.weatherBreakdown).reduce(
    (sum, w) => sum + w.totalKilled,
    0
  );

  elements.xpathMetric1.textContent = totalInjured.toLocaleString();
  elements.xpathLabel1.textContent = "Total Injured";
  elements.xpathMetric2.textContent = totalKilled.toLocaleString();
  elements.xpathLabel2.textContent = "Total Killed";

  // Chart 1: Weather breakdown
  const weatherLabels = Object.keys(results.weatherBreakdown);
  const weatherCounts = Object.values(results.weatherBreakdown).map(
    (w) => w.count
  );

  destroyXPathCharts();
  elements.xpathChart1Title.textContent = "Accidents by Weather Condition";
  xpathCharts.chart1 = createPieChart(
    elements.xpathChart1,
    weatherLabels,
    weatherCounts,
    "Accidents"
  );

  // Chart 2: Casualties by weather
  const casualtyData = Object.entries(results.weatherBreakdown).map(
    ([weather, stats]) => ({
      weather,
      injured: stats.totalInjured,
      killed: stats.totalKilled,
    })
  );

  elements.xpathChart2Title.textContent = "Casualties by Weather";
  xpathCharts.chart2 = createBarChart(
    elements.xpathChart2,
    casualtyData.map((d) => d.weather),
    [
      {
        label: "Injured",
        data: casualtyData.map((d) => d.injured),
        backgroundColor: "rgba(255, 159, 64, 0.6)",
      },
      {
        label: "Killed",
        data: casualtyData.map((d) => d.killed),
        backgroundColor: "rgba(255, 99, 132, 0.6)",
      },
    ]
  );

  // Table
  renderXPathTable(
    ["Weather", "Accidents", "Injured", "Killed", "Avg Casualties"],
    Object.entries(results.weatherBreakdown).map(([weather, stats]) => [
      weather,
      stats.count,
      stats.totalInjured,
      stats.totalKilled,
      ((stats.totalInjured + stats.totalKilled) / stats.count).toFixed(2),
    ])
  );
}

function renderVulnerableUsersResults(results, queryInfo) {
  // Update header
  elements.xpathQueryTitle.textContent = queryInfo.title;
  elements.xpathQueryDescription.textContent = queryInfo.description;
  elements.xpathExpression.textContent = queryInfo.xpath;

  // Update summary cards
  const totalAccidents = Object.values(results.weatherImpact).reduce(
    (sum, w) => sum + w.accidents,
    0
  );
  elements.xpathTotalResults.textContent = totalAccidents.toLocaleString();
  document.getElementById("xpath-total-label").textContent = "Accidents";

  elements.xpathMetric1.textContent = results.totalPedestrians.toLocaleString();
  elements.xpathLabel1.textContent = "Pedestrian Casualties";
  elements.xpathMetric2.textContent = results.totalCyclists.toLocaleString();
  elements.xpathLabel2.textContent = "Cyclist Casualties";

  // Chart 1: Distribution by user type and weather
  const topWeathers = results.mostDangerousWeather.slice(0, 5);
  const weatherLabels = topWeathers.map(([weather]) => weather);

  destroyXPathCharts();
  elements.xpathChart1Title.textContent =
    "Top 5 Most Dangerous Weather Conditions";
  xpathCharts.chart1 = createBarChart(elements.xpathChart1, weatherLabels, [
    {
      label: "Pedestrians",
      data: topWeathers.map(
        ([, stats]) => stats.pedestrians.injured + stats.pedestrians.killed
      ),
      backgroundColor: "rgba(75, 192, 192, 0.6)",
    },
    {
      label: "Cyclists",
      data: topWeathers.map(
        ([, stats]) => stats.cyclists.injured + stats.cyclists.killed
      ),
      backgroundColor: "rgba(153, 102, 255, 0.6)",
    },
  ]);

  // Chart 2: Pie chart of total vulnerable users
  elements.xpathChart2Title.textContent = "Vulnerable User Distribution";
  xpathCharts.chart2 = createPieChart(
    elements.xpathChart2,
    ["Pedestrians", "Cyclists"],
    [results.totalPedestrians, results.totalCyclists],
    "Casualties"
  );

  // Table
  renderXPathTable(
    ["Weather", "Accidents", "Pedestrians", "Cyclists", "Total Casualties"],
    Object.entries(results.weatherImpact).map(([weather, stats]) => [
      weather,
      stats.accidents,
      stats.pedestrians.injured + stats.pedestrians.killed,
      stats.cyclists.injured + stats.cyclists.killed,
      stats.pedestrians.injured +
        stats.pedestrians.killed +
        stats.cyclists.injured +
        stats.cyclists.killed,
    ])
  );
}

function renderMultiVehicleResults(results, queryInfo) {
  // Update header
  elements.xpathQueryTitle.textContent = queryInfo.title;
  elements.xpathQueryDescription.textContent = queryInfo.description;
  elements.xpathExpression.textContent = queryInfo.xpath;

  // Update summary cards
  elements.xpathTotalResults.textContent =
    results.totalMultiVehicleAccidents.toLocaleString();
  document.getElementById("xpath-total-label").textContent =
    "Multi-Vehicle Accidents";

  elements.xpathMetric1.textContent = results.totalCasualties.toLocaleString();
  elements.xpathLabel1.textContent = "Total Casualties";
  elements.xpathMetric2.textContent = results.avgCasualtiesPerAccident;
  elements.xpathLabel2.textContent = "Avg Casualties/Accident";

  // Chart 1: Top contributing factors
  const topFactors = results.topFactors.slice(0, 10);
  destroyXPathCharts();
  elements.xpathChart1Title.textContent = "Top 10 Contributing Factors";
  xpathCharts.chart1 = createHorizontalBarChart(
    elements.xpathChart1,
    topFactors.map((f) => f.factor),
    topFactors.map((f) => f.count),
    "Accidents"
  );

  // Chart 2: Casualties by factor
  elements.xpathChart2Title.textContent = "Casualties by Contributing Factor";
  xpathCharts.chart2 = createBarChart(
    elements.xpathChart2,
    topFactors.slice(0, 8).map((f) => f.factor.substring(0, 20) + "..."),
    [
      {
        label: "Casualties",
        data: topFactors.slice(0, 8).map((f) => f.casualties),
        backgroundColor: "rgba(255, 99, 132, 0.6)",
      },
    ]
  );

  // Table
  renderXPathTable(
    [
      "Contributing Factor",
      "Accidents",
      "Casualties",
      "Avg Vehicles",
      "Risk Score",
    ],
    topFactors.map((f) => [
      f.factor,
      f.count,
      f.casualties,
      f.avgVehicles,
      ((f.casualties / f.count) * parseFloat(f.avgVehicles)).toFixed(2),
    ])
  );
}

function renderXPathTable(headers, rows) {
  // Clear existing content
  elements.xpathTableHead.innerHTML = "";
  elements.xpathTableBody.innerHTML = "";

  // Add headers
  const headerRow = document.createElement("tr");
  headers.forEach((header) => {
    const th = document.createElement("th");
    th.textContent = header;
    headerRow.appendChild(th);
  });
  elements.xpathTableHead.appendChild(headerRow);

  // Add rows
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    row.forEach((cell) => {
      const td = document.createElement("td");
      td.textContent = cell;
      tr.appendChild(td);
    });
    elements.xpathTableBody.appendChild(tr);
  });
}

function destroyXPathCharts() {
  if (xpathCharts.chart1) {
    xpathCharts.chart1.destroy();
    xpathCharts.chart1 = null;
  }
  if (xpathCharts.chart2) {
    xpathCharts.chart2.destroy();
    xpathCharts.chart2 = null;
  }
}

// ============================================================
// START APPLICATION
// ============================================================

document.addEventListener("DOMContentLoaded", init);
