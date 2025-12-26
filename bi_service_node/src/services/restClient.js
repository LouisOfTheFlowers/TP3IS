/**
 * REST Client - Communicates with XML Service via REST API
 * Replaces GraphQL with direct REST calls
 */

const axios = require("axios");

const XML_SERVICE_URL =
  process.env.XML_SERVICE_URL || "http://xml-service:5000/api";

/**
 * Execute a REST GET request to XML Service
 * @param {string} endpoint - API endpoint path
 * @param {object} params - Query parameters
 * @returns {Promise<object>} Response data
 */
async function get(endpoint, params = {}) {
  try {
    const response = await axios.get(`${XML_SERVICE_URL}${endpoint}`, {
      params,
      timeout: 120000, // 2 minutes for large datasets
    });

    if (!response.data.success) {
      throw new Error(response.data.error || "Request failed");
    }

    return response.data.data;
  } catch (error) {
    if (error.response) {
      throw new Error(
        `XML Service error: ${error.response.status} - ${
          error.response.data?.error || error.message
        }`
      );
    }
    throw error;
  }
}

/**
 * Execute a REST POST request to XML Service
 * @param {string} endpoint - API endpoint path
 * @param {object} body - Request body
 * @returns {Promise<object>} Response data
 */
async function post(endpoint, body = {}) {
  try {
    const response = await axios.post(`${XML_SERVICE_URL}${endpoint}`, body, {
      headers: {
        "Content-Type": "application/json",
      },
      timeout: 120000,
    });

    if (!response.data.success) {
      throw new Error(response.data.error || "Request failed");
    }

    return response.data.data;
  } catch (error) {
    if (error.response) {
      throw new Error(
        `XML Service error: ${error.response.status} - ${
          error.response.data?.error || error.message
        }`
      );
    }
    throw error;
  }
}

// ============================================================
// API Service Methods
// ============================================================

const restClient = {
  /**
   * Get summary statistics
   */
  getStatistics: () => get("/statistics"),

  /**
   * Get weather-accident correlation
   */
  getWeatherCorrelation: () => get("/weather-correlation"),

  /**
   * Get casualties by weather condition
   * @param {string} weatherFilter - Optional weather condition filter
   */
  getCasualtiesByWeather: (weatherFilter = null) => {
    const params = weatherFilter ? { weather: weatherFilter } : {};
    return get("/casualties-by-weather", params);
  },

  /**
   * Get contributing factors
   * @param {number} limit - Number of results to return
   */
  getContributingFactors: (limit = 20) =>
    get("/contributing-factors", { limit }),

  /**
   * Get time period analysis
   * @param {string} startDate - Start date (ISO format)
   * @param {string} endDate - End date (ISO format)
   * @param {string} groupBy - Group by (hour, day, month, year)
   */
  getTimePeriod: (startDate = null, endDate = null, groupBy = "hour") => {
    const params = { groupBy };
    if (startDate) params.startDate = startDate;
    if (endDate) params.endDate = endDate;
    return get("/time-period", params);
  },

  /**
   * Get vehicle types analysis
   * @param {number} limit - Number of results to return
   */
  getVehicleTypes: (limit = 15) => get("/vehicle-types", { limit }),

  /**
   * Execute custom XPath query
   * @param {string} query - XPath expression
   * @param {number} limit - Result limit
   */
  executeXPath: (query, limit = 100) => post("/xpath/query", { query, limit }),

  /**
   * Get dashboard data (all at once)
   * @param {boolean} quick - Return cached data
   */
  getDashboard: (quick = false) => get("/dashboard", { quick }),
};

module.exports = { restClient };
