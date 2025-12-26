/**
 * API Routes - REST endpoints for BI Service
 * Protocol D: REST for Visualization communication
 */

const express = require("express");
const router = express.Router();
const { restClient } = require("../services/restClient");

// ============================================================
// GET /api/health - Health check
// ============================================================
router.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    service: "bi-service-nodejs",
    timestamp: new Date().toISOString(),
  });
});

// ============================================================
// GET /api/statistics - Summary statistics
// ============================================================
router.get("/statistics", async (req, res, next) => {
  try {
    const data = await restClient.getStatistics();
    res.json({
      success: true,
      data: data,
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================
// GET /api/weather-correlation - Weather-accident correlation
// ============================================================
router.get("/weather-correlation", async (req, res, next) => {
  try {
    const data = await restClient.getWeatherCorrelation();

    res.json({
      success: true,
      data: data,
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================
// GET /api/casualties-by-weather - Casualties grouped by weather
// ============================================================
router.get("/casualties-by-weather", async (req, res, next) => {
  try {
    const { weather } = req.query;
    const data = await restClient.getCasualtiesByWeather(weather || null);

    res.json({
      success: true,
      data: data,
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================
// GET /api/contributing-factors - Top contributing factors
// ============================================================
router.get("/contributing-factors", async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit) || 20;
    const data = await restClient.getContributingFactors(limit);

    res.json({
      success: true,
      data: data,
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================
// GET /api/time-period - Accidents by time period
// ============================================================
router.get("/time-period", async (req, res, next) => {
  try {
    const { startDate, endDate, groupBy = "hour" } = req.query;

    const data = await restClient.getTimePeriod(
      startDate || null,
      endDate || null,
      groupBy
    );

    res.json({
      success: true,
      groupBy,
      data: data,
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================
// GET /api/vehicle-types - Accidents by vehicle type
// ============================================================
router.get("/vehicle-types", async (req, res, next) => {
  try {
    const limit = parseInt(req.query.limit) || 15;
    const data = await restClient.getVehicleTypes(limit);

    res.json({
      success: true,
      data: data,
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================
// GET /api/dashboard - All dashboard data in one call
// ============================================================
router.get("/dashboard", async (req, res, next) => {
  try {
    const quick = req.query.quick === "true";

    if (quick) {
      // Return mock/cached data immediately for initial page load
      res.json({
        success: true,
        cached: true,
        data: {
          statistics: {
            totalCollisions: 100000,
            totalInjured: 25000,
            totalKilled: 250,
            totalDocuments: 1000,
          },
          weatherCorrelation: [
            {
              weatherCondition: "Clear",
              totalAccidents: 15000,
              totalInjured: 3000,
              totalKilled: 50,
              pedestriansInjured: 500,
              cyclistsInjured: 300,
              avgInjuredPerAccident: 0.2,
              avgKilledPerAccident: 0.003,
              fatalityRatePer1000: 3.3,
            },
            {
              weatherCondition: "Rain",
              totalAccidents: 8000,
              totalInjured: 2000,
              totalKilled: 40,
              pedestriansInjured: 400,
              cyclistsInjured: 250,
              avgInjuredPerAccident: 0.25,
              avgKilledPerAccident: 0.005,
              fatalityRatePer1000: 5.0,
            },
            {
              weatherCondition: "Snow",
              totalAccidents: 2000,
              totalInjured: 600,
              totalKilled: 15,
              pedestriansInjured: 100,
              cyclistsInjured: 50,
              avgInjuredPerAccident: 0.3,
              avgKilledPerAccident: 0.0075,
              fatalityRatePer1000: 7.5,
            },
          ],
          contributingFactors: [
            {
              contributingFactor: "Driver Inattention/Distraction",
              accidentCount: 12000,
              percentage: 30.0,
            },
            {
              contributingFactor: "Following Too Closely",
              accidentCount: 8000,
              percentage: 20.0,
            },
            {
              contributingFactor: "Failure to Yield Right-of-Way",
              accidentCount: 6000,
              percentage: 15.0,
            },
          ],
          vehicleTypes: [
            { vehicleType: "Sedan", involvementCount: 25000, percentage: 40.0 },
            { vehicleType: "SUV", involvementCount: 15000, percentage: 24.0 },
            { vehicleType: "Taxi", involvementCount: 10000, percentage: 16.0 },
          ],
        },
      });
      return;
    }

    // Execute all queries in parallel for full data
    const [stats, weather, factors, vehicles] = await Promise.all([
      restClient.getStatistics(),
      restClient.getWeatherCorrelation(),
      restClient.getContributingFactors(10),
      restClient.getVehicleTypes(10),
    ]);

    res.json({
      success: true,
      data: {
        statistics: stats,
        weatherCorrelation: weather,
        contributingFactors: factors,
        vehicleTypes: vehicles,
      },
    });
  } catch (error) {
    next(error);
  }
});

// ============================================================
// POST /api/load-data - Trigger data loading with duplicate checking
// ============================================================
router.post("/load-data", async (req, res, next) => {
  try {
    // Call the data processor's load endpoint
    const dataProcessorUrl =
      (process.env.DATA_PROCESSOR_URL || "http://data-processor:8001") +
      "/load-data";
    console.log(`[Load Data] Calling ${dataProcessorUrl}`);

    const response = await require("axios").post(
      dataProcessorUrl,
      {},
      { timeout: 120000 } // 2 minute timeout for data loading
    );

    res.json({
      success: true,
      message: response.data.message || "Data loaded successfully",
      details: response.data,
    });
  } catch (error) {
    console.error("[Load Data Error]:", error.message);
    res.status(500).json({
      success: false,
      message: "Failed to load data: " + error.message,
    });
  }
});

// ============================================================
// POST /api/webhook - Webhook endpoint for XML Service notifications
// ============================================================
router.post("/webhook", (req, res) => {
  console.log("[Webhook] Received notification:", req.body);

  const { request_id, status, document_id, timestamp } = req.body;

  // Here you could emit WebSocket events, store in cache, etc.
  console.log(`[Webhook] Document ${document_id} - Status: ${status}`);

  res.json({
    received: true,
    timestamp: new Date().toISOString(),
  });
});

// ============================================================
// POST /api/xpath - Execute XPath query (proxy to XML Service)
// ============================================================
router.post("/xpath", async (req, res, next) => {
  try {
    const { query, limit } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        error: "XPath query is required",
      });
    }

    const data = await restClient.executeXPath(query, limit || 100);

    res.json({
      success: true,
      data: data,
    });
  } catch (error) {
    console.error("[XPath Error]:", error.message);
    next(error);
  }
});

module.exports = router;
