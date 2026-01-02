/**
 * XPath Query Service - Complex XPath queries for collision data analysis
 * These queries demonstrate XPath capabilities on the hierarchical XML structure
 */

const XML_SERVICE_URL = "/api/xpath";

class XPathQueryService {
  constructor() {
    this.xmlServiceUrl = XML_SERVICE_URL;
  }

  /**
   * Execute a raw XPath query against all documents using REST API
   */
  async executeXPath(xpathQuery, limit = 100) {
    try {
      console.log("[XPath Frontend] Executing query:", xpathQuery);
      const response = await fetch(this.xmlServiceUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: xpathQuery,
          limit: limit,
        }),
      });

      console.log("[XPath Frontend] Response status:", response.status);
      const result = await response.json();
      console.log("[XPath Frontend] Result:", result);

      if (!result.success) {
        throw new Error(result.error || "XPath query failed");
      }

      return result.data;
    } catch (error) {
      console.error("XPath Query Error:", error);
      throw error;
    }
  }

  /**
   * COMPLEX QUERY 1: High-Risk Accidents Analysis
   * Find accidents with multiple casualties in specific weather conditions
   * Returns: Accidents with 3+ injuries OR any fatalities during Rain/Snow
   */
  async getHighRiskAccidents() {
    const xpathQuery = `
      //col:collision[
        col:weather/col:condition[contains(text(), 'Rain') or contains(text(), 'Snow')] 
        and (
          col:casualties/col:personsInjured >= 3 
          or col:casualties/col:personsKilled > 0
        )
      ]
    `;

    const results = await this.executeXPath(xpathQuery);
    return this.processHighRiskResults(results);
  }

  /**
   * COMPLEX QUERY 2: Vulnerable Road Users in Adverse Weather
   * Find accidents involving pedestrians or cyclists during bad weather (not Clear)
   * Returns: Casualties breakdown by weather condition for vulnerable users
   */
  async getVulnerableUsersInAdverseWeather() {
    const xpathQuery = `
      //col:collision[
        col:weather/col:condition[not(contains(text(), 'Clear'))]
        and (
          col:casualties/col:pedestriansInjured > 0
          or col:casualties/col:pedestriansKilled > 0
          or col:casualties/col:cyclistsInjured > 0
          or col:casualties/col:cyclistsKilled > 0
        )
      ]
    `;

    const results = await this.executeXPath(xpathQuery);
    return this.processVulnerableUsersResults(results);
  }

  /**
   * COMPLEX QUERY 3: Multi-Vehicle Accidents with Specific Factors
   * Find accidents involving 3+ vehicles with specific contributing factors
   * Returns: Correlation between vehicle count, factors, and severity
   */
  async getMultiVehicleFactorAnalysis() {
    const xpathQuery = `
      //col:collision[
        count(col:vehicles/col:vehicle[text() != '']) >= 3
        and col:contributingFactors/col:factor[
          contains(text(), 'Distraction')
          or contains(text(), 'Speed')
          or contains(text(), 'Following Too Closely')
        ]
      ]
    `;

    const results = await this.executeXPath(xpathQuery);
    return this.processMultiVehicleResults(results);
  }

  /**
   * COMPLEX QUERY 4: Time-Weather-Severity Correlation
   * Find peak danger times by combining time of day with weather and casualties
   */
  async getTimeWeatherSeverityCorrelation() {
    const queries = {
      morning: `//col:collision[col:crashInfo/col:time[substring(text(), 1, 2) >= '06' and substring(text(), 1, 2) < '12']]`,
      afternoon: `//col:collision[col:crashInfo/col:time[substring(text(), 1, 2) >= '12' and substring(text(), 1, 2) < '18']]`,
      evening: `//col:collision[col:crashInfo/col:time[substring(text(), 1, 2) >= '18' and substring(text(), 1, 2) < '24']]`,
      night: `//col:collision[col:crashInfo/col:time[substring(text(), 1, 2) >= '00' and substring(text(), 1, 2) < '06']]`,
    };

    const results = {};
    for (const [period, query] of Object.entries(queries)) {
      results[period] = await this.executeXPath(query);
    }

    return this.processTimeWeatherCorrelation(results);
  }

  /**
   * COMPLEX QUERY 5: Factor Combinations Leading to Fatalities
   * Identify which combinations of contributing factors most often result in fatalities
   */
  async getFatalFactorCombinations() {
    const xpathQuery = `
      //col:collision[
        col:casualties/col:personsKilled > 0
        and count(col:contributingFactors/col:factor[text() != '']) >= 2
      ]
    `;

    const results = await this.executeXPath(xpathQuery);
    return this.processFatalFactorCombinations(results);
  }

  /**
   * Process results for High-Risk Accidents query
   */
  processHighRiskResults(xpathResults) {
    const accidents = [];
    const weatherStats = {};

    xpathResults.forEach((doc) => {
      doc.result.forEach((xmlString) => {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlString, "text/xml");

        const collision = {
          date: xmlDoc.querySelector("crashInfo date")?.textContent,
          time: xmlDoc.querySelector("crashInfo time")?.textContent,
          weather:
            xmlDoc.querySelector("weather condition")?.textContent || "Unknown",
          injured: parseInt(
            xmlDoc.querySelector("casualties personsInjured")?.textContent || 0
          ),
          killed: parseInt(
            xmlDoc.querySelector("casualties personsKilled")?.textContent || 0
          ),
          factors: Array.from(
            xmlDoc.querySelectorAll("contributingFactors factor")
          ).map((f) => f.textContent),
        };

        accidents.push(collision);

        // Aggregate by weather
        if (!weatherStats[collision.weather]) {
          weatherStats[collision.weather] = {
            count: 0,
            totalInjured: 0,
            totalKilled: 0,
          };
        }
        weatherStats[collision.weather].count++;
        weatherStats[collision.weather].totalInjured += collision.injured;
        weatherStats[collision.weather].totalKilled += collision.killed;
      });
    });

    return {
      totalHighRiskAccidents: accidents.length,
      weatherBreakdown: weatherStats,
      recentAccidents: accidents.slice(0, 10), // Top 10 most recent
    };
  }

  /**
   * Process results for Vulnerable Users query
   */
  processVulnerableUsersResults(xpathResults) {
    const weatherImpact = {};
    let totalPedestrians = 0;
    let totalCyclists = 0;

    xpathResults.forEach((doc) => {
      doc.result.forEach((xmlString) => {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlString, "text/xml");

        const weather =
          xmlDoc.querySelector("weather condition")?.textContent || "Unknown";
        const pedInjured = parseInt(
          xmlDoc.querySelector("casualties pedestriansInjured")?.textContent ||
            0
        );
        const pedKilled = parseInt(
          xmlDoc.querySelector("casualties pedestriansKilled")?.textContent || 0
        );
        const cycInjured = parseInt(
          xmlDoc.querySelector("casualties cyclistsInjured")?.textContent || 0
        );
        const cycKilled = parseInt(
          xmlDoc.querySelector("casualties cyclistsKilled")?.textContent || 0
        );

        if (!weatherImpact[weather]) {
          weatherImpact[weather] = {
            pedestrians: { injured: 0, killed: 0 },
            cyclists: { injured: 0, killed: 0 },
            accidents: 0,
          };
        }

        weatherImpact[weather].pedestrians.injured += pedInjured;
        weatherImpact[weather].pedestrians.killed += pedKilled;
        weatherImpact[weather].cyclists.injured += cycInjured;
        weatherImpact[weather].cyclists.killed += cycKilled;
        weatherImpact[weather].accidents++;

        totalPedestrians += pedInjured + pedKilled;
        totalCyclists += cycInjured + cycKilled;
      });
    });

    return {
      weatherImpact,
      totalPedestrians,
      totalCyclists,
      mostDangerousWeather: Object.entries(weatherImpact)
        .sort((a, b) => {
          const aTotal =
            a[1].pedestrians.injured +
            a[1].pedestrians.killed +
            a[1].cyclists.injured +
            a[1].cyclists.killed;
          const bTotal =
            b[1].pedestrians.injured +
            b[1].pedestrians.killed +
            b[1].cyclists.injured +
            b[1].cyclists.killed;
          return bTotal - aTotal;
        })
        .slice(0, 5),
    };
  }

  /**
   * Process results for Multi-Vehicle Accidents query
   */
  processMultiVehicleResults(xpathResults) {
    const factorCounts = {};
    let totalAccidents = 0;
    let totalCasualties = 0;

    xpathResults.forEach((doc) => {
      doc.result.forEach((xmlString) => {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlString, "text/xml");

        const factors = Array.from(
          xmlDoc.querySelectorAll("contributingFactors factor")
        ).map((f) => f.textContent);
        const vehicles = Array.from(xmlDoc.querySelectorAll("vehicles vehicle"))
          .filter((v) => v.textContent.trim())
          .map((v) => v.textContent);
        const injured = parseInt(
          xmlDoc.querySelector("casualties personsInjured")?.textContent || 0
        );
        const killed = parseInt(
          xmlDoc.querySelector("casualties personsKilled")?.textContent || 0
        );

        totalAccidents++;
        totalCasualties += injured + killed;

        factors.forEach((factor) => {
          if (!factorCounts[factor]) {
            factorCounts[factor] = {
              count: 0,
              casualties: 0,
              vehicleCount: 0,
            };
          }
          factorCounts[factor].count++;
          factorCounts[factor].casualties += injured + killed;
          factorCounts[factor].vehicleCount += vehicles.length;
        });
      });
    });

    return {
      totalMultiVehicleAccidents: totalAccidents,
      totalCasualties,
      avgCasualtiesPerAccident: (totalCasualties / totalAccidents).toFixed(2),
      topFactors: Object.entries(factorCounts)
        .sort((a, b) => b[1].count - a[1].count)
        .slice(0, 10)
        .map(([factor, stats]) => ({
          factor,
          ...stats,
          avgVehicles: (stats.vehicleCount / stats.count).toFixed(1),
        })),
    };
  }

  /**
   * Process Time-Weather correlation results
   */
  processTimeWeatherCorrelation(periodResults) {
    const analysis = {};

    for (const [period, xpathResults] of Object.entries(periodResults)) {
      const weatherStats = {};
      let totalAccidents = 0;
      let totalCasualties = 0;

      xpathResults.forEach((doc) => {
        doc.result.forEach((xmlString) => {
          const parser = new DOMParser();
          const xmlDoc = parser.parseFromString(xmlString, "text/xml");

          const weather =
            xmlDoc.querySelector("weather condition")?.textContent || "Unknown";
          const injured = parseInt(
            xmlDoc.querySelector("casualties personsInjured")?.textContent || 0
          );
          const killed = parseInt(
            xmlDoc.querySelector("casualties personsKilled")?.textContent || 0
          );

          if (!weatherStats[weather]) {
            weatherStats[weather] = { count: 0, casualties: 0 };
          }

          weatherStats[weather].count++;
          weatherStats[weather].casualties += injured + killed;
          totalAccidents++;
          totalCasualties += injured + killed;
        });
      });

      analysis[period] = {
        totalAccidents,
        totalCasualties,
        avgSeverity: (totalCasualties / totalAccidents).toFixed(2),
        weatherBreakdown: weatherStats,
      };
    }

    return analysis;
  }

  /**
   * Process Fatal Factor Combinations
   */
  processFatalFactorCombinations(xpathResults) {
    const combinations = {};

    xpathResults.forEach((doc) => {
      doc.result.forEach((xmlString) => {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlString, "text/xml");

        const factors = Array.from(
          xmlDoc.querySelectorAll("contributingFactors factor")
        )
          .map((f) => f.textContent)
          .filter((f) => f.trim())
          .sort();

        const killed = parseInt(
          xmlDoc.querySelector("casualties personsKilled")?.textContent || 0
        );

        if (factors.length >= 2) {
          const comboKey = factors.join(" + ");
          if (!combinations[comboKey]) {
            combinations[comboKey] = { count: 0, totalKilled: 0 };
          }
          combinations[comboKey].count++;
          combinations[comboKey].totalKilled += killed;
        }
      });
    });

    return Object.entries(combinations)
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, 15)
      .map(([combo, stats]) => ({
        factors: combo,
        accidents: stats.count,
        fatalities: stats.totalKilled,
        fatalityRate: ((stats.totalKilled / stats.count) * 100).toFixed(1),
      }));
  }
}

export const xpathQueryService = new XPathQueryService();
