/**
 * Chart Factory - Creates and manages Chart.js charts
 */

// Color palettes
const COLORS = {
  primary: "rgba(37, 99, 235, 1)",
  primaryLight: "rgba(37, 99, 235, 0.2)",
  secondary: "rgba(100, 116, 139, 1)",
  success: "rgba(34, 197, 94, 1)",
  warning: "rgba(245, 158, 11, 1)",
  danger: "rgba(239, 68, 68, 1)",
  palette: [
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
  ],
};

// Store chart instances for cleanup
const chartInstances = {};

/**
 * Destroy existing chart before creating new one
 */
function destroyChart(canvasId) {
  if (chartInstances[canvasId]) {
    chartInstances[canvasId].destroy();
    delete chartInstances[canvasId];
  }
}

/**
 * Create a bar chart
 */
export function createBarChart(canvasId, labels, datasets, options = {}) {
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;

  const chartConfig = {
    type: "bar",
    data: {
      labels: labels,
      datasets: datasets.map((dataset, idx) => ({
        label: dataset.label,
        data: dataset.data,
        backgroundColor:
          dataset.color || COLORS.palette[idx % COLORS.palette.length],
        borderColor: dataset.borderColor || "transparent",
        borderWidth: 1,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: datasets.length > 1,
          position: "top",
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
      ...options,
    },
  };

  chartInstances[canvasId] = new Chart(ctx, chartConfig);
  return chartInstances[canvasId];
}

/**
 * Create a line chart
 */
export function createLineChart(canvasId, labels, datasets, options = {}) {
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;

  const chartConfig = {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets.map((dataset, idx) => ({
        label: dataset.label,
        data: dataset.data,
        borderColor:
          dataset.color || COLORS.palette[idx % COLORS.palette.length],
        backgroundColor: dataset.backgroundColor || "transparent",
        fill: dataset.fill || false,
        tension: 0.3,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: "top",
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
      ...options,
    },
  };

  chartInstances[canvasId] = new Chart(ctx, chartConfig);
  return chartInstances[canvasId];
}

/**
 * Create a pie/doughnut chart
 */
export function createPieChart(canvasId, labels, data, options = {}) {
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;

  const chartConfig = {
    type: options.doughnut ? "doughnut" : "pie",
    data: {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: COLORS.palette,
          borderWidth: 2,
          borderColor: "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: "right",
        },
      },
      ...options,
    },
  };

  chartInstances[canvasId] = new Chart(ctx, chartConfig);
  return chartInstances[canvasId];
}

/**
 * Create a scatter chart
 */
export function createScatterChart(canvasId, data, options = {}) {
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;

  const chartConfig = {
    type: "scatter",
    data: {
      datasets: [
        {
          label: options.label || "Data Points",
          data: data,
          backgroundColor: COLORS.primary,
          pointRadius: 8,
          pointHoverRadius: 10,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const point = context.raw;
              return point.label
                ? `${point.label}: (${point.x}, ${point.y})`
                : `(${point.x}, ${point.y})`;
            },
          },
        },
      },
      scales: {
        x: {
          title: {
            display: true,
            text: options.xLabel || "X",
          },
        },
        y: {
          title: {
            display: true,
            text: options.yLabel || "Y",
          },
          beginAtZero: true,
        },
      },
      ...options,
    },
  };

  chartInstances[canvasId] = new Chart(ctx, chartConfig);
  return chartInstances[canvasId];
}

/**
 * Create a horizontal bar chart
 */
export function createHorizontalBarChart(
  canvasId,
  labels,
  datasets,
  options = {}
) {
  destroyChart(canvasId);

  const ctx = document.getElementById(canvasId)?.getContext("2d");
  if (!ctx) return null;

  const chartConfig = {
    type: "bar",
    data: {
      labels: labels,
      datasets: datasets.map((dataset, idx) => ({
        label: dataset.label,
        data: dataset.data,
        backgroundColor:
          dataset.color || COLORS.palette[idx % COLORS.palette.length],
      })),
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          display: datasets.length > 1,
        },
      },
      scales: {
        x: {
          beginAtZero: true,
        },
      },
      ...options,
    },
  };

  chartInstances[canvasId] = new Chart(ctx, chartConfig);
  return chartInstances[canvasId];
}

export { COLORS };
