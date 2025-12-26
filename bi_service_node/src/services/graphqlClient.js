/**
 * GraphQL Client - Communicates with XML Service
 */

const axios = require("axios");

const XML_SERVICE_URL =
  process.env.XML_SERVICE_URL || "http://localhost:5000/graphql";

/**
 * Execute a GraphQL query against the XML Service
 * @param {string} query - GraphQL query string
 * @param {object} variables - Query variables
 * @returns {Promise<object>} Query result data
 */
async function executeQuery(query, variables = {}) {
  try {
    const response = await axios.post(
      XML_SERVICE_URL,
      {
        query,
        variables,
      },
      {
        headers: {
          "Content-Type": "application/json",
        },
        timeout: 30000,
      }
    );

    if (response.data.errors) {
      throw new Error(response.data.errors[0].message);
    }

    return response.data.data;
  } catch (error) {
    if (error.response) {
      throw new Error(`XML Service error: ${error.response.status}`);
    }
    throw error;
  }
}

// ============================================================
// Pre-defined queries
// ============================================================

const queries = {
  summaryStatistics: `
        query {
            summaryStatistics {
                totalCollisions
                totalInjured
                totalKilled
                totalDocuments
            }
        }
    `,

  weatherCorrelation: `
        query {
            weatherAccidentCorrelation {
                weatherCondition
                totalAccidents
                totalInjured
                totalKilled
                pedestriansInjured
                cyclistsInjured
                avgInjuredPerAccident
                avgKilledPerAccident
                fatalityRatePer1000
            }
        }
    `,

  casualtiesByWeather: `
        query($weatherFilter: String) {
            casualtiesByWeather(weatherFilter: $weatherFilter) {
                weatherCondition
                totalAccidents
                totalInjured
                totalKilled
                avgCasualtiesPerAccident
            }
        }
    `,

  contributingFactors: `
        query($limit: Int) {
            accidentsByContributingFactor(limit: $limit) {
                contributingFactor
                accidentCount
                percentage
            }
        }
    `,

  timePeriodAnalysis: `
        query($startDate: String, $endDate: String, $groupBy: String) {
            accidentsByTimePeriod(startDate: $startDate, endDate: $endDate, groupBy: $groupBy) {
                period
                totalAccidents
                totalInjured
                totalKilled
            }
        }
    `,

  vehicleTypes: `
        query($limit: Int) {
            accidentsByVehicleType(limit: $limit) {
                vehicleType
                involvementCount
                percentage
            }
        }
    `,
};

module.exports = {
  executeQuery,
  queries,
};
