"""
GraphQL Schema Definition for XML Service
"""

type_defs = """
    type Query {
        # Document queries
        document(id: Int!): Document
        documentByRequestId(requestId: String!): Document
        documents(limit: Int = 100, offset: Int = 0): [DocumentSummary!]!
        
        # XPath query execution
        executeXPath(xpath: String!, documentId: Int): [XPathResult!]!
        
        # Complex analytical queries (for BI Service)
        casualtiesByWeather(weatherFilter: String): [WeatherCasualties!]!
        accidentsByContributingFactor(limit: Int = 20): [ContributingFactorStats!]!
        accidentsByTimePeriod(startDate: String, endDate: String, groupBy: String = "hour"): [TimePeriodStats!]!
        accidentsByVehicleType(limit: Int = 15): [VehicleTypeStats!]!
        weatherAccidentCorrelation: [WeatherCorrelation!]!
        summaryStatistics: SummaryStatistics!
    }
    
    type Mutation {
        # Create and store collision XML document
        createCollisionDocument(collisions: [CollisionInput!]!): DocumentResult!
        
        # Import from CSV data (for Data Processor)
        importCollisionsFromData(data: [CollisionInput!]!): DocumentResult!
    }
    
    # Input Types
    input CollisionInput {
        crash_date: String!
        crash_time: String
        persons_injured: Int
        persons_killed: Int
        pedestrians_injured: Int
        pedestrians_killed: Int
        cyclists_injured: Int
        cyclists_killed: Int
        motorists_injured: Int
        motorists_killed: Int
        factor_1: String
        factor_2: String
        factor_3: String
        factor_4: String
        factor_5: String
        vehicle_1: String
        vehicle_2: String
        vehicle_3: String
        vehicle_4: String
        vehicle_5: String
        weather_condition: String
    }
    
    # Document Types
    type Document {
        id: Int!
        requestId: String!
        xmlContent: String!
        status: String!
        validationErrors: String
        createdAt: String!
        mapperVersion: String!
    }
    
    type DocumentSummary {
        id: Int!
        requestId: String!
        status: String!
        createdAt: String!
        collisionCount: Int
        mapperVersion: String
    }
    
    type DocumentResult {
        requestId: String!
        status: String!
        documentId: Int
        error: String
    }
    
    # XPath Result
    type XPathResult {
        documentId: Int!
        result: [String!]!
    }
    
    # Analytical Query Types
    type WeatherCasualties {
        weatherCondition: String!
        totalAccidents: Int!
        totalInjured: Int!
        totalKilled: Int!
        avgCasualtiesPerAccident: Float!
    }
    
    type ContributingFactorStats {
        contributingFactor: String!
        accidentCount: Int!
        percentage: Float!
    }
    
    type TimePeriodStats {
        period: String!
        totalAccidents: Int!
        totalInjured: Int!
        totalKilled: Int!
    }
    
    type VehicleTypeStats {
        vehicleType: String!
        involvementCount: Int!
        percentage: Float!
    }
    
    type WeatherCorrelation {
        weatherCondition: String!
        totalAccidents: Int!
        totalInjured: Int!
        totalKilled: Int!
        pedestriansInjured: Int!
        cyclistsInjured: Int!
        avgInjuredPerAccident: Float!
        avgKilledPerAccident: Float!
        fatalityRatePer1000: Float!
    }
    
    type SummaryStatistics {
        totalCollisions: Int!
        totalInjured: Int!
        totalKilled: Int!
        totalDocuments: Int!
    }
"""
