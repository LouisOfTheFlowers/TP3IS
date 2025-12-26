/*
gRPC Service for Collision Data Analytics
Written in Go (3rd programming language)
This service provides gRPC endpoints that proxy requests to the XML Service via GraphQL

Protocol: gRPC (requirement #8d)
Language: Go (3rd language requirement #2)
*/
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"os"
	"time"

	pb "grpc_service/proto"

	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

const (
	defaultPort        = "50051"
	defaultXMLService  = "http://xml_service:5000/graphql"
	serviceVersion     = "1.0.0"
)

// Server implements the CollisionService gRPC server
type server struct {
	pb.UnimplementedCollisionServiceServer
	xmlServiceURL string
	httpClient    *http.Client
}

// GraphQL request/response structures
type GraphQLRequest struct {
	Query     string                 `json:"query"`
	Variables map[string]interface{} `json:"variables,omitempty"`
}

type GraphQLResponse struct {
	Data   json.RawMessage `json:"data"`
	Errors []struct {
		Message string `json:"message"`
	} `json:"errors,omitempty"`
}

// executeGraphQL sends a GraphQL query to the XML Service
func (s *server) executeGraphQL(ctx context.Context, query string, variables map[string]interface{}) (json.RawMessage, error) {
	reqBody := GraphQLRequest{
		Query:     query,
		Variables: variables,
	}
	
	jsonBody, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %v", err)
	}
	
	req, err := http.NewRequestWithContext(ctx, "POST", s.xmlServiceURL, bytes.NewBuffer(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")
	
	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to execute request: %v", err)
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %v", err)
	}
	
	var gqlResp GraphQLResponse
	if err := json.Unmarshal(body, &gqlResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal response: %v", err)
	}
	
	if len(gqlResp.Errors) > 0 {
		return nil, fmt.Errorf("GraphQL error: %s", gqlResp.Errors[0].Message)
	}
	
	return gqlResp.Data, nil
}

// HealthCheck implements health check endpoint
func (s *server) HealthCheck(ctx context.Context, req *pb.Empty) (*pb.HealthResponse, error) {
	return &pb.HealthResponse{
		Healthy:   true,
		Service:   "collision-grpc-service",
		Version:   serviceVersion,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	}, nil
}

// GetSummaryStatistics gets overall statistics
func (s *server) GetSummaryStatistics(ctx context.Context, req *pb.Empty) (*pb.SummaryStatisticsResponse, error) {
	query := `
		query {
			summaryStatistics {
				totalCollisions
				totalInjured
				totalKilled
				totalDocuments
			}
		}
	`
	
	data, err := s.executeGraphQL(ctx, query, nil)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		SummaryStatistics struct {
			TotalCollisions int32 `json:"totalCollisions"`
			TotalInjured    int32 `json:"totalInjured"`
			TotalKilled     int32 `json:"totalKilled"`
			TotalDocuments  int32 `json:"totalDocuments"`
		} `json:"summaryStatistics"`
	}
	
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %v", err)
	}
	
	return &pb.SummaryStatisticsResponse{
		TotalCollisions: result.SummaryStatistics.TotalCollisions,
		TotalInjured:    result.SummaryStatistics.TotalInjured,
		TotalKilled:     result.SummaryStatistics.TotalKilled,
		TotalDocuments:  result.SummaryStatistics.TotalDocuments,
	}, nil
}

// GetCasualtiesByWeather gets casualties grouped by weather condition
func (s *server) GetCasualtiesByWeather(ctx context.Context, req *pb.WeatherFilter) (*pb.WeatherCasualtiesResponse, error) {
	variables := make(map[string]interface{})
	filterPart := ""
	
	if req.WeatherCondition != "" {
		variables["weatherFilter"] = req.WeatherCondition
		filterPart = `(weatherFilter: $weatherFilter)`
	}
	
	query := fmt.Sprintf(`
		query($weatherFilter: String) {
			casualtiesByWeather%s {
				weatherCondition
				totalAccidents
				totalInjured
				totalKilled
				avgCasualtiesPerAccident
			}
		}
	`, filterPart)
	
	data, err := s.executeGraphQL(ctx, query, variables)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		CasualtiesByWeather []struct {
			WeatherCondition         string  `json:"weatherCondition"`
			TotalAccidents           int32   `json:"totalAccidents"`
			TotalInjured             int32   `json:"totalInjured"`
			TotalKilled              int32   `json:"totalKilled"`
			AvgCasualtiesPerAccident float64 `json:"avgCasualtiesPerAccident"`
		} `json:"casualtiesByWeather"`
	}
	
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %v", err)
	}
	
	response := &pb.WeatherCasualtiesResponse{
		Casualties: make([]*pb.WeatherCasualty, len(result.CasualtiesByWeather)),
	}
	
	for i, c := range result.CasualtiesByWeather {
		response.Casualties[i] = &pb.WeatherCasualty{
			WeatherCondition:         c.WeatherCondition,
			TotalAccidents:           c.TotalAccidents,
			TotalInjured:             c.TotalInjured,
			TotalKilled:              c.TotalKilled,
			AvgCasualtiesPerAccident: c.AvgCasualtiesPerAccident,
		}
	}
	
	return response, nil
}

// GetWeatherAccidentCorrelation gets weather-accident correlation data
func (s *server) GetWeatherAccidentCorrelation(ctx context.Context, req *pb.Empty) (*pb.WeatherCorrelationResponse, error) {
	query := `
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
	`
	
	data, err := s.executeGraphQL(ctx, query, nil)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		WeatherAccidentCorrelation []struct {
			WeatherCondition      string  `json:"weatherCondition"`
			TotalAccidents        int32   `json:"totalAccidents"`
			TotalInjured          int32   `json:"totalInjured"`
			TotalKilled           int32   `json:"totalKilled"`
			PedestriansInjured    int32   `json:"pedestriansInjured"`
			CyclistsInjured       int32   `json:"cyclistsInjured"`
			AvgInjuredPerAccident float64 `json:"avgInjuredPerAccident"`
			AvgKilledPerAccident  float64 `json:"avgKilledPerAccident"`
			FatalityRatePer1000   float64 `json:"fatalityRatePer1000"`
		} `json:"weatherAccidentCorrelation"`
	}
	
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %v", err)
	}
	
	response := &pb.WeatherCorrelationResponse{
		Correlations: make([]*pb.WeatherCorrelation, len(result.WeatherAccidentCorrelation)),
	}
	
	for i, c := range result.WeatherAccidentCorrelation {
		response.Correlations[i] = &pb.WeatherCorrelation{
			WeatherCondition:      c.WeatherCondition,
			TotalAccidents:        c.TotalAccidents,
			TotalInjured:          c.TotalInjured,
			TotalKilled:           c.TotalKilled,
			PedestriansInjured:    c.PedestriansInjured,
			CyclistsInjured:       c.CyclistsInjured,
			AvgInjuredPerAccident: c.AvgInjuredPerAccident,
			AvgKilledPerAccident:  c.AvgKilledPerAccident,
			FatalityRatePer_1000:  c.FatalityRatePer1000,
		}
	}
	
	return response, nil
}

// GetAccidentsByFactor gets accidents by contributing factor
func (s *server) GetAccidentsByFactor(ctx context.Context, req *pb.FactorRequest) (*pb.ContributingFactorResponse, error) {
	limit := req.Limit
	if limit == 0 {
		limit = 20
	}
	
	query := `
		query($limit: Int) {
			accidentsByContributingFactor(limit: $limit) {
				contributingFactor
				accidentCount
				percentage
			}
		}
	`
	
	variables := map[string]interface{}{
		"limit": limit,
	}
	
	data, err := s.executeGraphQL(ctx, query, variables)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		AccidentsByContributingFactor []struct {
			ContributingFactor string  `json:"contributingFactor"`
			AccidentCount      int32   `json:"accidentCount"`
			Percentage         float64 `json:"percentage"`
		} `json:"accidentsByContributingFactor"`
	}
	
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %v", err)
	}
	
	response := &pb.ContributingFactorResponse{
		Factors: make([]*pb.ContributingFactorStats, len(result.AccidentsByContributingFactor)),
	}
	
	for i, f := range result.AccidentsByContributingFactor {
		response.Factors[i] = &pb.ContributingFactorStats{
			ContributingFactor: f.ContributingFactor,
			AccidentCount:      f.AccidentCount,
			Percentage:         f.Percentage,
		}
	}
	
	return response, nil
}

// GetAccidentsByTimePeriod gets accidents by time period
func (s *server) GetAccidentsByTimePeriod(ctx context.Context, req *pb.TimePeriodRequest) (*pb.TimePeriodResponse, error) {
	groupBy := req.GroupBy
	if groupBy == "" {
		groupBy = "hour"
	}
	
	query := `
		query($startDate: String, $endDate: String, $groupBy: String) {
			accidentsByTimePeriod(startDate: $startDate, endDate: $endDate, groupBy: $groupBy) {
				hour
				date
				month
				totalAccidents
				totalInjured
				totalKilled
			}
		}
	`
	
	variables := map[string]interface{}{
		"startDate": req.StartDate,
		"endDate":   req.EndDate,
		"groupBy":   groupBy,
	}
	
	// Clean up empty values
	if req.StartDate == "" {
		delete(variables, "startDate")
	}
	if req.EndDate == "" {
		delete(variables, "endDate")
	}
	
	data, err := s.executeGraphQL(ctx, query, variables)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		AccidentsByTimePeriod []struct {
			Hour           string `json:"hour"`
			Date           string `json:"date"`
			Month          string `json:"month"`
			TotalAccidents int32  `json:"totalAccidents"`
			TotalInjured   int32  `json:"totalInjured"`
			TotalKilled    int32  `json:"totalKilled"`
		} `json:"accidentsByTimePeriod"`
	}
	
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %v", err)
	}
	
	response := &pb.TimePeriodResponse{
		Periods: make([]*pb.TimePeriodStats, len(result.AccidentsByTimePeriod)),
	}
	
	for i, p := range result.AccidentsByTimePeriod {
		timePeriod := p.Hour
		if groupBy == "date" {
			timePeriod = p.Date
		} else if groupBy == "month" {
			timePeriod = p.Month
		}
		
		response.Periods[i] = &pb.TimePeriodStats{
			TimePeriod:     timePeriod,
			TotalAccidents: p.TotalAccidents,
			TotalInjured:   p.TotalInjured,
			TotalKilled:    p.TotalKilled,
		}
	}
	
	return response, nil
}

// GetAccidentsByVehicleType gets accidents by vehicle type
func (s *server) GetAccidentsByVehicleType(ctx context.Context, req *pb.VehicleTypeRequest) (*pb.VehicleTypeResponse, error) {
	limit := req.Limit
	if limit == 0 {
		limit = 15
	}
	
	query := `
		query($limit: Int) {
			accidentsByVehicleType(limit: $limit) {
				vehicleType
				involvementCount
				percentage
			}
		}
	`
	
	variables := map[string]interface{}{
		"limit": limit,
	}
	
	data, err := s.executeGraphQL(ctx, query, variables)
	if err != nil {
		return nil, err
	}
	
	var result struct {
		AccidentsByVehicleType []struct {
			VehicleType      string  `json:"vehicleType"`
			InvolvementCount int32   `json:"involvementCount"`
			Percentage       float64 `json:"percentage"`
		} `json:"accidentsByVehicleType"`
	}
	
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %v", err)
	}
	
	response := &pb.VehicleTypeResponse{
		Vehicles: make([]*pb.VehicleTypeStats, len(result.AccidentsByVehicleType)),
	}
	
	for i, v := range result.AccidentsByVehicleType {
		response.Vehicles[i] = &pb.VehicleTypeStats{
			VehicleType:      v.VehicleType,
			InvolvementCount: v.InvolvementCount,
			Percentage:       v.Percentage,
		}
	}
	
	return response, nil
}

func main() {
	// Get configuration from environment
	port := os.Getenv("GRPC_PORT")
	if port == "" {
		port = defaultPort
	}
	
	xmlServiceURL := os.Getenv("XML_SERVICE_URL")
	if xmlServiceURL == "" {
		xmlServiceURL = defaultXMLService
	}
	
	// Create TCP listener
	lis, err := net.Listen("tcp", fmt.Sprintf(":%s", port))
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}
	
	// Create gRPC server
	grpcServer := grpc.NewServer()
	
	// Create and register service
	srv := &server{
		xmlServiceURL: xmlServiceURL,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
	pb.RegisterCollisionServiceServer(grpcServer, srv)
	
	// Enable reflection for tools like grpcurl
	reflection.Register(grpcServer)
	
	log.Printf("🚀 gRPC Service starting on port %s", port)
	log.Printf("📡 Connected to XML Service at %s", xmlServiceURL)
	
	// Start server
	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("Failed to serve: %v", err)
	}
}
