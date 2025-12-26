# 🚀 Load Data Feature - Complete Guide

## ✅ What's Been Updated

### 1. **Frontend - Debug Logging Added** 🔍

**File:** `front/js/main.js`

Added comprehensive console logging to track the entire Load Data workflow:

- 🔵 Button click event
- 🔵 API request sending
- 🔵 Response status and data
- ✅ Success messages with steps completed
- ❌ Detailed error logging with stack traces
- 🔵 Dashboard reload status

**How to view:** Open browser DevTools (F12) → Console tab → Click "Load Data" button

### 2. **Supabase Bucket Name Updated** 📦

**Files:**

- `crawler/upload_to_supabase.py`
- `crawler/load_to_database.py`

Changed bucket name from `"Data"` to `"dataBucket"` to match your Supabase configuration.

### 3. **Database Connection Verified** ✅

Your `.env` file is correctly configured with:

- ✅ **SUPABASE_URL:** https://bkqyppmkssdqwmfjhzop.supabase.co
- ✅ **SUPABASE_KEY:** Valid anon key (eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...)
- ✅ **DB_HOST:** aws-1-eu-west-1.pooler.supabase.com (Transaction Pooler - IPv4 compatible)
- ✅ **DB_PORT:** 6543
- ✅ **DB_USER:** postgres.bkqyppmkssdqwmfjhzop
- ✅ **DB_PASSWORD:** chEaHLOaqbwlxGeA

---

## 🎯 Complete Load Data Workflow

When you click the **"Load Data"** button, here's the complete process:

### **Step 1: Fetch Collision Data** 🕷️

- Calls NYC Open Data API
- Fetches 5,000 most recent collision records
- Creates `collisions_raw.csv` in data_processor container
- **API:** https://data.cityofnewyork.us/resource/h9gi-nx95.json

### **Step 2: Enrich with Weather** 🌤️

- Fetches hourly weather data from Visual Crossing API
- Matches weather conditions to collision times
- Creates `collisions_weather.csv`
- **API Key:** SCGJPXXX588GV6FRGVJTWLKYN

### **Step 3: Upload to Supabase Storage** 📤

- Uploads `collisions_weather.csv` to Supabase Storage
- **Bucket:** `dataBucket`
- **Authentication:** Uses SUPABASE_KEY from `.env`

### **Step 4: Load to PostgreSQL Database** 💾

- Downloads CSV from Supabase Storage bucket
- Parses CSV into collision records
- Sends data to XML Service via GraphQL mutation
- XML Service creates XML document and stores in `collision_documents` table
- Data is now queryable and visible in dashboard!

---

## 🧪 How to Test

### 1. **Open Browser Console**

```
1. Go to http://localhost:8080
2. Press F12 to open DevTools
3. Click "Console" tab
```

### 2. **Click Load Data Button**

You should see detailed logs like:

```
🔵 [Load Data] Button clicked
🔵 [Load Data] Button disabled, making API call...
🔵 [Load Data] Sending POST to /api/load-data
🔵 [Load Data] Response received: {status: 200, statusText: "OK", ok: true}
🔵 [Load Data] Response JSON: {success: true, message: "...", steps_completed: [...]}
✅ [Load Data] Success! Successfully scraped collision data...
✅ [Load Data] Steps completed: ["Fetched collision data...", "Enriched with weather...", ...]
🔵 [Load Data] Reloading dashboard data...
✅ [Load Data] Dashboard data reloaded
🔵 [Load Data] Button re-enabled
```

### 3. **Check Backend Logs**

```bash
# Check data_processor logs
docker logs data_processor --tail 100

# You should see:
# 🕷️ Step 1: Fetching collision data from NYC Open Data API...
# ✅ Collision data fetched successfully
# 🌤️ Step 2: Enriching collision data with weather information...
# ✅ Weather data enriched successfully
# 📤 Step 3: Uploading enriched data to Supabase bucket...
# ✅ Data uploaded to Supabase bucket successfully
# 💾 Step 4: Loading data from bucket to PostgreSQL database...
# ✅ Data loaded to database successfully
```

### 4. **Verify in Supabase**

1. Go to Supabase Dashboard → Storage → `dataBucket`
2. You should see `collisions_weather.csv` file
3. Go to Table Editor → `collision_documents` table
4. You should see new records with XML documents

### 5. **Verify in Frontend**

After clicking Load Data and seeing success:

1. Dashboard cards should update with new totals
2. Charts should display data
3. "Last Update" timestamp should show current time

---

## 🐛 Troubleshooting

### **Issue: No logs in console**

- Make sure DevTools Console is open BEFORE clicking button
- Check if JavaScript errors appear (red text)
- Verify frontend container is running: `docker ps`

### **Issue: 404 Error**

- Check BI Service logs: `docker logs bi_service --tail 50`
- Verify DATA_PROCESSOR_URL: `docker exec bi_service env | grep DATA_PROCESSOR`
- Should be: `http://data-processor:8001`

### **Issue: 403 Unauthorized (Supabase)**

- Verify SUPABASE_KEY in `.env` is correct
- Check data_processor has the key: `docker exec data_processor env | grep SUPABASE_KEY`
- Key should start with: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

### **Issue: Weather API fails**

- Verify WEATHER_API_KEY: `docker exec data_processor env | grep WEATHER_API_KEY`
- Should be: `SCGJPXXX588GV6FRGVJTWLKYN`
- Check Visual Crossing API quota (free tier has limits)

### **Issue: Database connection fails**

- Verify XML Service can connect to database
- Check logs: `docker logs xml_service --tail 50`
- Verify connection string in `.env` matches Supabase Transaction Pooler settings

---

## 📊 Expected Results

After successful load:

### **Database Tables**

- `collision_documents` - Contains XML documents with collision data
- `webhook_logs` - Tracks webhook notifications
- `processing_history` - Tracks data processing operations

### **Supabase Storage**

- `dataBucket/collisions_weather.csv` - Enriched CSV file (5000 records)

### **Dashboard**

- **Total Collisions:** 5000 (or current count)
- **Total Injured:** Sum of all injuries
- **Total Killed:** Sum of all fatalities
- **Total Documents:** Number of XML documents created

### **Console Output (Success)**

```
✅ [Load Data] Success! Successfully scraped collision data, enriched with weather, uploaded to Supabase, and loaded to database!
✅ [Load Data] Steps completed:
   [
     "Fetched collision data from NYC Open Data",
     "Enriched with weather information",
     "Uploaded to Supabase bucket",
     "Loaded to PostgreSQL database"
   ]
```

---

## 🔧 Configuration Files

All configuration is centralized in `.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://bkqyppmkssdqwmfjhzop.supabase.co
SUPABASE_KEY=eyJhbGci...

# Database Configuration (Transaction Pooler - IPv4)
DB_HOST=aws-1-eu-west-1.pooler.supabase.com
DB_PORT=6543
DB_NAME=postgres
DB_USER=postgres.bkqyppmkssdqwmfjhzop
DB_PASSWORD=chEaHLOaqbwlxGeA

# Weather API
WEATHER_API_KEY=SCGJPXXX588GV6FRGVJTWLKYN
```

---

## 📝 Next Steps

1. **Click Load Data button** in your browser
2. **Open Console (F12)** to see debug logs
3. **Wait 2-3 minutes** for complete processing
4. **Check dashboard** for updated data
5. **Verify Supabase Storage** has the CSV file
6. **Check database tables** for new records

---

## 🎉 Success Indicators

✅ Console shows all 4 steps completed
✅ Green success notification appears in UI
✅ Dashboard numbers update
✅ "Last Update" timestamp changes
✅ Supabase Storage has `collisions_weather.csv`
✅ Database table `collision_documents` has new records
✅ No red errors in console or backend logs

---

**Need help?** Check the console logs first, then backend logs with `docker logs data_processor --tail 100`
