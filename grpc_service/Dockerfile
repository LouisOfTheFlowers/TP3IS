# gRPC Service Dockerfile
# Language: Go
# Protocol: gRPC
FROM golang:alpine AS builder

# Install protoc and plugins
RUN apk add --no-cache protobuf-dev make

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum* ./

# Download dependencies
RUN go mod download

# Install protoc-gen-go plugins
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
RUN go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Copy source code
COPY . .

# Create proto directory
RUN mkdir -p proto

# Generate Go code from proto file
RUN protoc --go_out=./proto --go_opt=paths=source_relative \
    --go-grpc_out=./proto --go-grpc_opt=paths=source_relative \
    collision.proto

# Update dependencies after proto generation
RUN go mod tidy

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o grpc_server .

# Production image
FROM alpine

RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/grpc_server .

# Expose gRPC port
EXPOSE 50051

# Environment variables
ENV GRPC_PORT=50051
ENV XML_SERVICE_URL=http://xml-service:5000/graphql

CMD ["./grpc_server"]
