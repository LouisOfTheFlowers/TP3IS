/**
 * BI Service - REST API (Node.js/Express)
 * Protocol D: REST for Visualization communication
 * Protocol C: REST for XML Service communication
 */

const express = require("express");
const cors = require("cors");
const dotenv = require("dotenv");
const apiRoutes = require("./routes/api");

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5001;

// Middleware
app.use(
  cors({
    origin: process.env.ALLOWED_ORIGINS?.split(",") || "*",
  })
);
app.use(express.json());

// Logging middleware
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
  next();
});

// Routes
app.use("/api", apiRoutes);

// Health check
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    service: "bi-service-nodejs",
    version: "1.0.0",
    timestamp: new Date().toISOString(),
  });
});

// Root endpoint
app.get("/", (req, res) => {
  res.json({
    service: "BI Service (Node.js)",
    version: "1.0.0",
    protocol: "REST",
    endpoints: {
      health: "/health",
      statistics: "/api/statistics",
      weatherCorrelation: "/api/weather-correlation",
      contributingFactors: "/api/contributing-factors",
      timePeriodAnalysis: "/api/time-period",
      vehicleTypes: "/api/vehicle-types",
      dashboard: "/api/dashboard",
    },
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error("Error:", err.message);
  res.status(500).json({
    error: "Internal Server Error",
    message: err.message,
  });
});

// Start server
app.listen(PORT, "0.0.0.0", () => {
  console.log("=".repeat(60));
  console.log("🚀 BI SERVICE (Node.js) - REST API");
  console.log("=".repeat(60));
  console.log(`   Port: ${PORT}`);
  console.log(`   Protocol D: REST (to Visualization)`);
  console.log(`   Protocol C: REST (to XML Service)`);
  console.log(
    `   XML Service: ${
      process.env.XML_SERVICE_URL || "http://xml-service:5000/api"
    }`
  );
  console.log("=".repeat(60));
});

module.exports = app;
