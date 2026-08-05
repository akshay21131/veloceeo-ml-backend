# 🧠 Veloceeo ML Semantic Search Microservice

A Python FastAPI semantic search service powered by `sentence-transformers` (`all-MiniLM-L6-v2`) and live Supabase PostgreSQL database integration.

---

## 🚀 Quickstart: How to Run Locally

### 1. Navigate to the directory
```bash
cd ~/Desktop/Veloceeo/mlsearch
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the ML service
```bash
python main.py
```
*(On startup, `main.py` connects to your Supabase database, loads all live products & stores, and computes 384-dimensional vector embeddings).*

Output on successful startup:
```text
🔄 Fetching live products & stores from Supabase PostgreSQL database...
✅ Loaded 7 live products and 4 live stores from Supabase!
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 🧪 How to Test the Service

### Method A: Interactive Swagger API Docs (Browser)
Open your browser and navigate to:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**
- Click `POST /predict` ➔ `Try it out`
- Enter payload `{"query": "white cotton shirt"}` ➔ Click `Execute`.

### Method B: Health Check Endpoint (Browser)
Open your browser to:
👉 **[http://localhost:8000/health](http://localhost:8000/health)**

### Method C: Terminal Curl Request
In a separate terminal window:
```bash
curl -X POST 'http://localhost:8000/predict' \
  -H 'Content-Type: application/json' \
  -d '{"query": "nike running shoes"}'
```

Response returned:
```json
{
  "product_ids": [10, 16],
  "store_ids": [53]
}
```

---

## 🔄 Re-indexing Live Products
Whenever new products or stores are added to your Supabase database, trigger a re-index without restarting the server:

```bash
curl -X POST 'http://localhost:8000/reload'
```

---

## ☁️ Cloud Deployment (Docker)

Deploy using Docker on Railway, Render, Google Cloud Run, or Modal:

```bash
docker build -t veloceeo-ml-search .
docker run -p 8000:8000 veloceeo-ml-search
```

---

## ⚡ Supabase Edge Function Integration

After deploying your ML service to the cloud:
1. Open your Supabase Dashboard ➔ **Edge Functions** ➔ `search-products-stores`.
2. Replace its contents with the code inside **`ml_edge_function.ts`**.
3. Set environment variable `ML_SERVICE_URL` to your deployed ML server URL (e.g. `https://your-ml-app.up.railway.app/predict`).
