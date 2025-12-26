/**
 * API Routes - REST endpoints for BI Service
 */

const express = require("express");
const router = express.Router();
const { executeQuery, queries } = require("../services/graphqlClient");

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
    const data = await executeQuery(queries.summaryStatistics);
    res.json({
      success: true,
      data: data.summaryStatistics,
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
    const data = await executeQuery(queries.weatherCorrelation);

    // Transform data for frontend charts
    const correlations = data.weatherAccidentCorrelation.map((item) => ({
      weatherCondition: item.weatherCondition,
      totalAccidents: item.totalAccidents,
      totalInjured: item.totalInjured,
      totalKilled: item.totalKilled,
      pedestriansInjured: item.pedestriansInjured,
      cyclistsInjured: item.cyclistsInjured,
      avgInjuredPerAccident: parseFloat(item.avgInjuredPerAccident) || 0,
      avgKilledPerAccident: parseFloat(item.avgKilledPerAccident) || 0,
      fatalityRatePer1000: parseFloat(item.fatalityRatePer1000) || 0,
    }));

    res.json({
      success: true,
      data: correlations,
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
    const data = await executeQuery(queries.casualtiesByWeather, {
      weatherFilter: weather || null,
    });

    res.json({
      success: true,
      data: data.casualtiesByWeather,
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
    const data = await executeQuery(queries.contributingFactors, { limit });

    res.json({
      success: true,
      data: data.accidentsByContributingFactor,
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

    const data = await executeQuery(queries.timePeriodAnalysis, {
      startDate: startDate || null,
      endDate: endDate || null,
      groupBy,
    });

    // Transform based on groupBy
    const periods = data.accidentsByTimePeriod.map((item) => ({
      period: item.period,
      totalAccidents: item.totalAccidents,
      totalInjured: item.totalInjured,
      totalKilled: item.totalKilled,
    }));

    res.json({
      success: true,
      groupBy,
      data: periods,
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
    const data = await executeQuery(queries.vehicleTypes, { limit });

    res.json({
      success: true,
      data: data.accidentsByVehicleType,
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
    // Execute all queries in parallel
    const [stats, weather, factors, vehicles] = await Promise.all([
      executeQuery(queries.summaryStatistics),
      executeQuery(queries.weatherCorrelation),
      executeQuery(queries.contributingFactors, { limit: 10 }),
      executeQuery(queries.vehicleTypes, { limit: 10 }),
    ]);

    res.json({
      success: true,
      data: {
        statistics: stats.summaryStatistics,
        weatherCorrelation: weather.weatherAccidentCorrelation,
        contributingFactors: factors.accidentsByContributingFactor,
        vehicleTypes: vehicles.accidentsByVehicleType,
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

module.exports = router;
