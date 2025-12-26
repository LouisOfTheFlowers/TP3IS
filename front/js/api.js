/**
 * API Service - Handles all communication with BI Service
 */

const API_BASE_URL = "/api";

class APIService {
  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async fetch(endpoint, options = {}) {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success === false) {
        throw new Error(data.error || "Unknown error occurred");
      }

      return data.data || data;
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  async healthCheck() {
    return this.fetch("/health");
  }

  async getDashboard() {
    return this.fetch("/dashboard");
  }

  async getStatistics() {
    return this.fetch("/statistics");
  }

  async getWeatherCorrelation() {
    return this.fetch("/weather-correlation");
  }

  async getCasualtiesByWeather(filter = null) {
    const params = filter ? `?weather=${encodeURIComponent(filter)}` : "";
    return this.fetch(`/casualties-by-weather${params}`);
  }

  async getContributingFactors(limit = 20) {
    return this.fetch(`/contributing-factors?limit=${limit}`);
  }

  async getTimePeriod(startDate = null, endDate = null, groupBy = "hour") {
    const params = new URLSearchParams();
    if (startDate) params.append("startDate", startDate);
    if (endDate) params.append("endDate", endDate);
    params.append("groupBy", groupBy);
    return this.fetch(`/time-period?${params.toString()}`);
  }

  async getVehicleTypes(limit = 15) {
    return this.fetch(`/vehicle-types?limit=${limit}`);
  }
}

export const apiService = new APIService();
