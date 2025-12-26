# NYC Collision Data Analytics Platform

## 🚀 Quick Start with Docker

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd TP3IS

# 2. Copy environment file and configure
cp .env.example .env
# Edit .env with your Supabase credentials

# 3. Build and run all services
docker-compose up --build

# 4. Access the services:
# - Frontend:     http://localhost:8080
# - BI Service:   http://localhost:5001
# - XML Service:  http://localhost:5000
# - XML-RPC:      http://localhost:8000
# - gRPC:         localhost:50051
```

## 📋 Environment Configuration

Create a `.env` file in the project root (use `.env.example` as template):

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_key

# Database (Supabase PostgreSQL)
DB_HOST=db.your-project.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
```

## 🏗️ Architecture Overview

```
┌─────────────────┐                    ┌─────────────────┐
│     Crawler     │ ──────────────────►│    Supabase     │
│  (Python/Scrapy)│     S3 API         │    Bucket       │
└─────────────────┘                    └────────┬────────┘
                                                │
                                                ▼
┌─────────────────┐                    ┌─────────────────┐
│  Data Processor │◄───────────────────│  (CSV Download) │
│  (XML-RPC:8000) │                    └─────────────────┘
└────────┬────────┘
         │ GraphQL
         ▼
┌─────────────────┐     GraphQL        ┌─────────────────┐
│   BI Service    │◄──────────────────►│   XML Service   │
│  (REST:5001)    │                    │  (GraphQL:5000) │
│   [Node.js]     │                    │    [Python]     │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │ REST                                 │ SQL/XML
         ▼                                      ▼
┌─────────────────┐                    ┌─────────────────┐
│    Frontend     │                    │    Supabase     │
│   (Nginx:8080)  │                    │   PostgreSQL    │
│  [JavaScript]   │                    │  (XML Column)   │
└─────────────────┘                    └─────────────────┘

         ┌─────────────────┐
         │  gRPC Service   │◄── gRPC Clients
         │   (Go:50051)    │
         └─────────────────┘
```

## 🔧 Services

| Service        | Port  | Protocol | Language   | Description                            |
| -------------- | ----- | -------- | ---------- | -------------------------------------- |
| XML Service    | 5000  | GraphQL  | Python     | XML mapping, validation, XPath queries |
| BI Service     | 5001  | REST     | Node.js    | Data transformation, API for frontend  |
| gRPC Service   | 50051 | gRPC     | Go         | Alternative API access                 |
| Data Processor | 8000  | XML-RPC  | Python     | Process data from Supabase bucket      |
| Frontend       | 8080  | HTTP     | JavaScript | Dashboard visualization                |

## 📊 Features

- **Manual XML Mapper** - Custom XML generation (not auto-generated)
- **XSD Validation** - Schema validation for all XML documents
- **5 Complex XPath Queries** - Weather correlation, time analysis, etc.
- **4 Protocols** - REST, GraphQL, gRPC, XML-RPC
- **3 Languages** - Python, Node.js, Go

## 🐳 Docker Commands

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f xml-service

# Stop all services
docker-compose down

# Rebuild specific service
docker-compose up --build xml-service
```

## Services

### 1. XML Service (Port 5000)

- **Technology**: Python, Flask, Ariadne (GraphQL)
- **Database**: PostgreSQL with XML column type
- **Features**:
  - Manual XML mapping (not auto-generated)
  - XML validation against XSD schema
  - XPath queries on stored XML documents
  - GraphQL API for complex queries

### 2. BI Service (Port 5001)

- **Technology**: Node.js, Express
- **Protocol**: REST API
- **Features**:
  - Data aggregation and transformation
  - Weather-accident correlation analysis
  - Formatted responses for visualization

### 3. Frontend (Port 8080)

- **Technology**: JavaScript, Vite, Chart.js
- **Features**:
  - Summary dashboard
  - Weather-accident correlation visualization
  - Contributing factors analysis
  - Time-based trends

## Complex Queries (XPath-based)

### Query 1: Casualties by Weather Condition

```graphql
query {
  casualtiesByWeather(weatherFilter: "Rain") {
    weatherCondition
    totalAccidents
    totalInjured
    totalKilled
    avgCasualtiesPerAccident
  }
}
```

### Query 2: Accidents by Contributing Factor

```graphql
query {
  accidentsByContributingFactor(limit: 20) {
    contributingFactor
    accidentCount
    percentage
  }
}
```

### Query 3: Time-based Analysis

```graphql
query {
  accidentsByTimePeriod(
    startDate: "2024-01-01"
    endDate: "2024-12-31"
    groupBy: "month"
  ) {
    period
    totalAccidents
    totalInjured
    totalKilled
  }
}
```

## Setup Instructions

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for local development)

### Quick Start with Docker

1. **Clone and navigate to project**:

   ```bash
   cd TP3IS
   ```

2. **Start all services**:

   ```bash
   docker-compose up -d
   ```

3. **Start frontend** (development):

   ```bash
   cd front
   npm install
   npm run dev
   ```

4. **Access services**:
   - Frontend: http://localhost:3000
   - BI Service API: http://localhost:5001
   - XML Service GraphQL: http://localhost:5000/graphql

### Local Development Setup

1. **Database** (PostgreSQL):

   ```bash
   docker run -d --name collision_db \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=collision_db \
     -p 5432:5432 \
     postgres:15
   ```

2. **XML Service**:

   ```bash
   cd xml_service
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your settings
   python app.py
   ```

3. **BI Service**:

   ```bash
   cd bi_service
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   python app.py
   ```

4. **Frontend**:
   ```bash
   cd front
   npm install
   npm run dev
   ```

---

## Original Crawler Pipeline

Small data pipeline that pulls NYC crash data, enriches it with hourly
weather, and uploads the final CSV to Supabase Storage.

### Crawler Requirements

- Python 3.9+
- Packages: `requests`, `pandas`, `python-dotenv`, `supabase`

### Crawler Setup

Create a `.env` file in the project root:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
WEATHER_API_KEY=your_visualcrossing_key
```

Install dependencies:

```
pip install requests pandas python-dotenv supabase
```

### Run Crawler

1. Fetch collisions:

```
python crawler/fetch_collisions.py
```

Creates `collisions_raw.csv`.

2. Enrich with weather:

```
python crawler/enrich_with_weather.py
```

Creates `collisions_weather.csv`.

3. Upload to Supabase Storage:

```
python crawler/upload_to_supabase.py
```

---

## API Endpoints

### BI Service REST API

| Endpoint                             | Method | Description                  |
| ------------------------------------ | ------ | ---------------------------- |
| `/api/health`                        | GET    | Health check                 |
| `/api/dashboard`                     | GET    | Full dashboard data          |
| `/api/dashboard/summary`             | GET    | Summary statistics           |
| `/api/analysis/weather-impact`       | GET    | Weather impact analysis      |
| `/api/analysis/contributing-factors` | GET    | Contributing factors         |
| `/api/analysis/time-trends`          | GET    | Time-based analysis          |
| `/api/analysis/weather-correlation`  | GET    | Weather-accident correlation |
| `/api/analysis/vehicle-types`        | GET    | Vehicle type statistics      |

### XML Service GraphQL

Access GraphiQL explorer at: `http://localhost:5000/graphql`

## Data Flow

1. **Crawler** fetches collision data from NYC Open Data API
2. **Crawler** enriches data with weather information
3. **Data Processor** receives CSV and sends to XML Service
4. **XML Service** creates XML, validates against schema, stores in PostgreSQL
5. **XML Service** sends webhook notification with status
6. **BI Service** queries XML Service using GraphQL
7. **BI Service** transforms data for visualization
8. **Frontend** displays interactive charts and tables

## XML Schema

The collision data is structured in XML format with the following elements:

- `collisionDataset` (root)
  - `metadata` (source, timestamp, record count)
  - `collisions` (list of collision records)
    - `collision` (individual accident)
      - `crashInfo` (date, time)
      - `casualties` (injured/killed counts)
      - `contributingFactors` (up to 5 factors)
      - `vehicles` (up to 5 vehicle types)
      - `weather` (weather condition)

## Project Structure

```
TP3IS/
├── crawler/                 # Data collection scripts
├── xml_service/            # XML/GraphQL service
│   ├── config/             # Configuration
│   ├── database/           # Database management
│   ├── graphql/            # GraphQL schema & resolvers
│   ├── services/           # Business logic
│   ├── xml/                # XML mapping & validation
│   │   └── schema/         # XSD schema
│   ├── app.py              # Main application
│   └── Dockerfile
├── bi_service/             # BI REST API service
│   ├── config/             # Configuration
│   ├── routes/             # API routes
│   ├── services/           # Data transformation
│   ├── app.py              # Main application
│   └── Dockerfile
├── front/                  # Frontend visualization
│   ├── js/                 # JavaScript modules
│   ├── styles/             # CSS styles
│   └── index.html          # Main HTML
├── docker-compose.yml      # Docker orchestration
└── README.md
```

## Data Sources

- NYC Open Data: Motor Vehicle Collisions (`h9gi-nx95`)
- Visual Crossing Weather API (hourly conditions per day)

## License

This project is developed for educational purposes as part of TP3IS course.
