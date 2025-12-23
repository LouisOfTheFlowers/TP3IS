# TP3 Collision Pipeline

Small data pipeline that pulls NYC crash data, enriches it with hourly
weather, and uploads the final CSV to Supabase Storage.

## Requirements
- Python 3.9+
- Packages: `requests`, `pandas`, `python-dotenv`, `supabase`

## Setup
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

## Run
1) Fetch collisions:
```
python crawler/fetch_collisions.py
```
Creates `collisions_raw.csv`.

2) Enrich with weather:
```
python crawler/enrich_with_weather.py
```
Creates `collisions_weather.csv`.

3) Upload to Supabase Storage:
```
python crawler/upload_to_supabase.py
```

## Data Sources
- NYC Open Data: Motor Vehicle Collisions (`h9gi-nx95`)
- Visual Crossing Weather API (hourly conditions per day)

## Outputs
- `collisions_raw.csv` (raw collisions selection)
- `collisions_weather.csv` (collisions with `weather_condition`)
