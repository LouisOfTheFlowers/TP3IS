"""
GraphQL Resolvers for XML Service
"""
from ariadne import QueryType, MutationType
from services.collision_service import collision_service
from services.xpath_query_service import xpath_query_service

# Create resolver instances
query = QueryType()
mutation = MutationType()


# ============================================================
# QUERY RESOLVERS
# ============================================================

@query.field("document")
def resolve_document(_, info, id):
    """Get document by ID"""
    doc = collision_service.get_document_by_id(id)
    if doc:
        return {
            "id": doc["id"],
            "requestId": doc["request_id"],
            "xmlContent": doc["xml_documento"],
            "status": doc["status"],
            "validationErrors": doc["validation_errors"],
            "createdAt": str(doc["data_criacao"]),
            "mapperVersion": doc["mapper_version"]
        }
    return None


@query.field("documentByRequestId")
def resolve_document_by_request_id(_, info, requestId):
    """Get document by request ID"""
    doc = collision_service.get_document_by_request_id(requestId)
    if doc:
        return {
            "id": doc["id"],
            "requestId": doc["request_id"],
            "xmlContent": doc["xml_documento"],
            "status": doc["status"],
            "validationErrors": doc["validation_errors"],
            "createdAt": str(doc["data_criacao"]),
            "mapperVersion": doc["mapper_version"]
        }
    return None


@query.field("documents")
def resolve_documents(_, info, limit=100, offset=0):
    """Get all documents with pagination"""
    docs = collision_service.get_all_documents(limit, offset)
    return [{
        "id": doc["id"],
        "requestId": doc["request_id"],
        "status": doc["status"],
        "createdAt": str(doc["data_criacao"]),
        "collisionCount": doc.get("collision_count", 0),
        "mapperVersion": doc.get("mapper_version", "1.0.0")
    } for doc in docs]


@query.field("executeXPath")
def resolve_execute_xpath(_, info, xpath, documentId=None):
    """Execute XPath query on documents"""
    results = xpath_query_service.execute_xpath(xpath, documentId)
    return [{
        "documentId": r["document_id"],
        "result": r["result"] if r["result"] else []
    } for r in results]


@query.field("casualtiesByWeather")
def resolve_casualties_by_weather(_, info, weatherFilter=None):
    """Get casualties grouped by weather condition"""
    results = xpath_query_service.get_casualties_by_weather(weatherFilter)
    return [{
        "weatherCondition": r["weather_condition"],
        "totalAccidents": r["total_accidents"],
        "totalInjured": r["total_injured"],
        "totalKilled": r["total_killed"],
        "avgCasualtiesPerAccident": float(r["avg_casualties_per_accident"]) if r["avg_casualties_per_accident"] else 0.0
    } for r in results]


@query.field("accidentsByContributingFactor")
def resolve_accidents_by_contributing_factor(_, info, limit=20):
    """Get accidents grouped by contributing factor"""
    results = xpath_query_service.get_accidents_by_contributing_factor(limit)
    return [{
        "contributingFactor": r["contributing_factor"],
        "accidentCount": r["accident_count"],
        "percentage": float(r["percentage"]) if r["percentage"] else 0.0
    } for r in results]


@query.field("accidentsByTimePeriod")
def resolve_accidents_by_time_period(_, info, startDate=None, endDate=None, groupBy="hour"):
    """Get accidents grouped by time period"""
    results = xpath_query_service.get_accidents_by_time_period(startDate, endDate, groupBy)
    
    # Map the dynamic field name to 'period'
    period_key = groupBy if groupBy in ["hour", "date", "month"] else "hour"
    
    return [{
        "period": str(r.get(period_key, r.get("hour", r.get("date", r.get("month", ""))))),
        "totalAccidents": r["total_accidents"],
        "totalInjured": r["total_injured"],
        "totalKilled": r["total_killed"]
    } for r in results]


@query.field("accidentsByVehicleType")
def resolve_accidents_by_vehicle_type(_, info, limit=15):
    """Get accidents by vehicle type"""
    results = xpath_query_service.get_accidents_by_vehicle_type(limit)
    return [{
        "vehicleType": r["vehicle_type"],
        "involvementCount": r["involvement_count"],
        "percentage": float(r["percentage"]) if r["percentage"] else 0.0
    } for r in results]


@query.field("weatherAccidentCorrelation")
def resolve_weather_accident_correlation(_, info):
    """Get weather-accident correlation data"""
    results = xpath_query_service.get_weather_accident_correlation()
    return [{
        "weatherCondition": r["weather_condition"],
        "totalAccidents": r["total_accidents"],
        "totalInjured": r["total_injured"],
        "totalKilled": r["total_killed"],
        "pedestriansInjured": r["pedestrians_injured"],
        "cyclistsInjured": r["cyclists_injured"],
        "avgInjuredPerAccident": float(r["avg_injured_per_accident"]) if r["avg_injured_per_accident"] else 0.0,
        "avgKilledPerAccident": float(r["avg_killed_per_accident"]) if r["avg_killed_per_accident"] else 0.0,
        "fatalityRatePer1000": float(r["fatality_rate_per_1000"]) if r["fatality_rate_per_1000"] else 0.0
    } for r in results]


@query.field("summaryStatistics")
def resolve_summary_statistics(_, info):
    """Get summary statistics"""
    stats = xpath_query_service.get_summary_statistics()
    return {
        "totalCollisions": stats["total_collisions"] or 0,
        "totalInjured": stats["total_injured"] or 0,
        "totalKilled": stats["total_killed"] or 0,
        "totalDocuments": stats["total_documents"] or 0
    }


# ============================================================
# MUTATION RESOLVERS
# ============================================================

@mutation.field("createCollisionDocument")
def resolve_create_collision_document(_, info, collisions):
    """Create a new collision XML document"""
    # Convert GraphQL input to dictionaries
    collision_data = [dict(c) for c in collisions]
    
    result = collision_service.process_and_store_collisions(collision_data)
    
    return {
        "requestId": result["request_id"],
        "status": result["status"],
        "documentId": result["document_id"],
        "error": result["error"]
    }


@mutation.field("importCollisionsFromData")
def resolve_import_collisions_from_data(_, info, data):
    """Import collision data (typically from Data Processor)"""
    collision_data = [dict(d) for d in data]
    
    result = collision_service.process_and_store_collisions(collision_data)
    
    return {
        "requestId": result["request_id"],
        "status": result["status"],
        "documentId": result["document_id"],
        "error": result["error"]
    }


# Export resolvers
resolvers = [query, mutation]
