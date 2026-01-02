/**
 * XPath Queries Module for app.html
 * Handles custom XPath query execution and display
 */

const API_BASE = "/api";

// ==================== XPATH QUERIES ====================
export const xpathQueries = {
  // Predefined queries with proper namespaces
  queries: {
    1: {
      query:
        "//col:collision[col:weather/col:condition[contains(text(), 'Rain') or contains(text(), 'Snow') or contains(text(), 'Fog')]]",
      name: "Weather-Related Collisions",
      description:
        "Find all collisions that occurred during rain, snow, or fog conditions",
    },
    2: {
      query:
        "//col:collision[col:weather/col:condition[not(contains(text(), 'Rain')) and not(contains(text(), 'Snow')) and not(contains(text(), 'Fog'))]]",
      name: "Non-Weather Collisions",
      description:
        "Find all collisions that occurred in clear or other conditions",
    },
    3: {
      query: "//col:collision[count(col:vehicles/col:vehicle) >= 3]",
      name: "Multi-Vehicle Accidents",
      description: "Find accidents involving 3 or more vehicles",
    },
    4: {
      query:
        "//col:collision[col:crashInfo/col:time[substring(text(), 1, 2) >= '18' or substring(text(), 1, 2) < '06']]",
      name: "Night-Time Collisions",
      description: "Find collisions that occurred between 6 PM and 6 AM",
    },
    5: {
      query: "//col:collision[col:casualties/col:personsKilled > 0]",
      name: "Fatal Accidents",
      description: "Find all accidents with fatalities",
    },
  },

  init() {
    console.log("[XPath] Initializing XPath module");

    // Set up event listeners for predefined query buttons
    document.querySelectorAll(".query-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const queryNum = e.currentTarget.dataset.query;
        console.log("[XPath] Predefined query button clicked:", queryNum);
        this.runPredefinedQuery(queryNum);
      });
    });

    // Set up custom query execution
    const executeBtn = document.getElementById("execute-xpath");
    if (executeBtn) {
      executeBtn.addEventListener("click", () => {
        console.log("[XPath] Execute custom query button clicked");
        this.runCustomQuery();
      });
    }

    // Allow Enter key in textarea to execute query
    const xpathInput = document.getElementById("xpath-input");
    if (xpathInput) {
      xpathInput.addEventListener("keydown", (e) => {
        if (e.ctrlKey && e.key === "Enter") {
          this.runCustomQuery();
        }
      });
    }
  },

  runPredefinedQuery(queryNum) {
    const queryInfo = this.queries[queryNum];
    if (!queryInfo) {
      console.error("[XPath] Unknown query number:", queryNum);
      return;
    }

    console.log("[XPath] Running predefined query:", queryInfo.name);

    // Set the query in the textarea
    document.getElementById("xpath-input").value = queryInfo.query;

    // Execute the query
    this.executeQuery(queryInfo.query, 100);
  },

  runCustomQuery() {
    const query = document.getElementById("xpath-input").value.trim();
    const limit = parseInt(document.getElementById("xpath-limit").value) || 100;

    if (!query) {
      this.showToast("Please enter an XPath query", "warning");
      return;
    }

    console.log("[XPath] Running custom query:", query);
    this.executeQuery(query, limit);
  },

  async executeQuery(query, limit) {
    const loadingOverlay = document.getElementById("loading-overlay");
    const statsContainer = document.getElementById("xpath-stats");
    const outputContainer = document.getElementById("xpath-output");

    try {
      // Show loading
      if (loadingOverlay) {
        loadingOverlay.classList.add("active");
      }

      console.log("[XPath] Sending request with query:", query);
      console.log("[XPath] Limit:", limit);

      // Execute the XPath query via API
      const response = await fetch(`${API_BASE}/xpath`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          limit: limit,
        }),
      });

      console.log("[XPath] Response status:", response.status);

      if (!response.ok) {
        throw new Error(
          `HTTP ${response.status}: ${response.statusText || "Request failed"}`
        );
      }

      const result = await response.json();
      console.log("[XPath] Result:", result);

      if (!result.success) {
        throw new Error(result.error || "Query execution failed");
      }

      // Display results
      this.displayResults(result, query);
      this.showToast("Query executed successfully", "success");
    } catch (error) {
      console.error("[XPath] Query error:", error);
      this.showToast(`Query failed: ${error.message}`, "error");

      if (statsContainer) {
        statsContainer.innerHTML = "";
      }

      if (outputContainer) {
        outputContainer.innerHTML = `
          <div style="padding: 1rem; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #fca5a5;">
            <strong>❌ Error:</strong> ${this.escapeHtml(error.message)}
          </div>
        `;
      }
    } finally {
      // Hide loading
      if (loadingOverlay) {
        loadingOverlay.classList.remove("active");
      }
    }
  },

  displayResults(result, query) {
    const statsContainer = document.getElementById("xpath-stats");
    const outputContainer = document.getElementById("xpath-output");

    if (!statsContainer || !outputContainer) {
      console.error("[XPath] Display containers not found");
      return;
    }

    const data = result.data || [];
    const resultCount = data.length;

    console.log("[XPath] Displaying results, count:", resultCount);

    // Display stats
    statsContainer.innerHTML = `
      <div style="display: flex; gap: 2rem; flex-wrap: wrap; margin-bottom: 1.5rem;">
        <div style="flex: 1; min-width: 150px; padding: 1rem; background: var(--surface-color, #1e293b); border-radius: 8px;">
          <div style="font-size: 2rem; font-weight: bold; color: var(--primary-color, #3b82f6);">${resultCount}</div>
          <div style="color: var(--text-muted, #94a3b8); margin-top: 0.25rem;">Results Found</div>
        </div>
        <div style="flex: 1; min-width: 150px; padding: 1rem; background: var(--surface-color, #1e293b); border-radius: 8px;">
          <div style="font-size: 1rem; font-weight: 500; color: var(--text-color, #e2e8f0); word-break: break-word;">${this.escapeHtml(
            query.substring(0, 100) + (query.length > 100 ? "..." : "")
          )}</div>
          <div style="color: var(--text-muted, #94a3b8); margin-top: 0.25rem;">Query Expression</div>
        </div>
      </div>
    `;

    // Display results
    if (resultCount === 0) {
      outputContainer.innerHTML = `
        <div style="padding: 2rem; text-align: center; color: var(--text-muted, #94a3b8);">
          <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
          <div style="font-size: 1.25rem; font-weight: 500;">No Results Found</div>
          <div style="margin-top: 0.5rem;">Try adjusting your XPath query</div>
        </div>
      `;
      return;
    }

    // Process results - data is array of {document_id, result}
    let resultsHtml = '<div class="xpath-results-grid">';

    data.forEach((item, index) => {
      const documentId = item.document_id || "N/A";
      const xmlResults = item.result || [];

      // Each result array contains XML strings
      xmlResults.forEach((xmlString, resultIndex) => {
        resultsHtml += this.formatXmlResult(
          xmlString,
          index * xmlResults.length + resultIndex + 1,
          documentId
        );
      });
    });

    resultsHtml += "</div>";
    outputContainer.innerHTML = resultsHtml;
  },

  formatXmlResult(xmlString, resultNumber, documentId) {
    // Parse XML to extract key information
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlString, "text/xml");

    // Check for parse errors
    const parseError = xmlDoc.querySelector("parsererror");
    if (parseError) {
      return `
        <div style="margin-bottom: 1rem; padding: 1rem; background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; border-radius: 8px;">
          <strong>Result #${resultNumber} - XML Parse Error</strong>
          <pre style="margin-top: 0.5rem; white-space: pre-wrap; color: #fca5a5;">${this.escapeHtml(
            xmlString
          )}</pre>
        </div>
      `;
    }

    // Extract collision information
    const collision = xmlDoc.querySelector("collision");
    if (!collision) {
      return `
        <div style="margin-bottom: 1rem; padding: 1rem; background: var(--surface-color, #1e293b); border-left: 4px solid var(--primary-color, #3b82f6); border-radius: 8px;">
          <strong>Result #${resultNumber}</strong> (Doc ID: ${documentId})
          <pre style="margin-top: 0.5rem; white-space: pre-wrap; font-size: 0.875rem;">${this.escapeHtml(
            xmlString
          )}</pre>
        </div>
      `;
    }

    // Extract key fields
    const date =
      collision.querySelector("crashInfo date")?.textContent || "N/A";
    const time =
      collision.querySelector("crashInfo time")?.textContent || "N/A";
    const borough =
      collision.querySelector("location borough")?.textContent || "N/A";
    const weather =
      collision.querySelector("weather condition")?.textContent || "N/A";
    const injured =
      collision.querySelector("casualties personsInjured")?.textContent || "0";
    const killed =
      collision.querySelector("casualties personsKilled")?.textContent || "0";
    const factors = Array.from(
      collision.querySelectorAll("contributingFactors factor")
    )
      .map((f) => f.textContent)
      .filter((f) => f.trim())
      .join(", ");

    return `
      <div style="margin-bottom: 1rem; padding: 1rem; background: var(--surface-color, #1e293b); border-left: 4px solid var(--primary-color, #3b82f6); border-radius: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
          <strong style="color: var(--text-color, #e2e8f0);">Result #${resultNumber}</strong>
          <span style="color: var(--text-muted, #94a3b8); font-size: 0.875rem;">Document ID: ${documentId}</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.75rem; margin-top: 0.75rem;">
          <div>
            <div style="color: var(--text-muted, #94a3b8); font-size: 0.875rem;">Date & Time</div>
            <div style="color: var(--text-color, #e2e8f0); font-weight: 500;">${this.escapeHtml(
              date
            )} ${this.escapeHtml(time)}</div>
          </div>
          <div>
            <div style="color: var(--text-muted, #94a3b8); font-size: 0.875rem;">Location</div>
            <div style="color: var(--text-color, #e2e8f0); font-weight: 500;">${this.escapeHtml(
              borough
            )}</div>
          </div>
          <div>
            <div style="color: var(--text-muted, #94a3b8); font-size: 0.875rem;">Weather</div>
            <div style="color: var(--text-color, #e2e8f0); font-weight: 500;">${this.escapeHtml(
              weather
            )}</div>
          </div>
          <div>
            <div style="color: var(--text-muted, #94a3b8); font-size: 0.875rem;">Casualties</div>
            <div style="color: var(--text-color, #e2e8f0); font-weight: 500;">
              ${injured} injured, ${killed} killed
            </div>
          </div>
        </div>
        ${
          factors
            ? `
        <div style="margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(148, 163, 184, 0.2);">
          <div style="color: var(--text-muted, #94a3b8); font-size: 0.875rem; margin-bottom: 0.25rem;">Contributing Factors</div>
          <div style="color: var(--text-color, #e2e8f0);">${this.escapeHtml(
            factors
          )}</div>
        </div>
        `
            : ""
        }
      </div>
    `;
  },

  showToast(message, type = "info") {
    // Create toast container if it doesn't exist
    let container = document.getElementById("toast-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "toast-container";
      container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        gap: 10px;
      `;
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    const colors = {
      info: "#3b82f6",
      success: "#10b981",
      warning: "#f59e0b",
      error: "#ef4444",
    };

    toast.style.cssText = `
      padding: 1rem 1.5rem;
      background: ${colors[type] || colors.info};
      color: white;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      animation: slideIn 0.3s ease;
      max-width: 300px;
    `;

    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = "slideOut 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  },

  escapeHtml(text) {
    const map = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
  },
};

// Auto-initialize when the XPath page becomes active
document.addEventListener("DOMContentLoaded", () => {
  // Initialize when page loads if we're on xpath page
  if (document.getElementById("page-xpath")) {
    xpathQueries.init();
    console.log("[XPath] Module initialized");
  }
});

// Also export for use in other modules
export default xpathQueries;
