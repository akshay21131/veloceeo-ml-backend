# 🚀 Complete Step-by-Step Guide: Deploying Veloceeo ML Microservices on Render.com

This guide provides step-by-step instructions to deploy both **Text/Voice ML Search** (`mlsearch`) and **Image ML Search** (`image search`) for free on **[Render.com](https://render.com)**.

---

## 📋 PRE-REQUISITE: Upload Code to GitHub

### Step 1: Create a GitHub Repository
1. Go to [github.com/new](https://github.com/new) and create a repository named **`veloceeo-ml-backend`**.
2. Upload/Push your **`Desktop/Veloceeo/mlsearch`** and **`Desktop/Veloceeo/image search`** folders to this repository.

---

## 🛠️ PART 1: Deploy Text & Voice ML Search (`mlsearch`)

### Step 1: Create Web Service on Render
1. Go to **[dashboard.render.com](https://dashboard.render.com)** and click **New +** ➔ **Web Service**.
2. Select **Build and deploy from a Git repository** ➔ Click **Next**.
3. Select your `veloceeo-ml-backend` repository.

### Step 2: Configure Service Details
Fill in the following fields:

- **Name**: `veloceeo-ml-search`
- **Region**: Oregon (US West) or Frankfurt (EU)
- **Root Directory**: `mlsearch`
- **Runtime**: `Python 3` (or `Docker`)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: Select **Free** (or Starter)

### Step 3: Set Environment Variables
Scroll down to **Environment Variables** and click **Add Environment Variable**:
- Key: `SUPABASE_URL` | Value: `https://cnqukpjrxrtqqrmertuo.supabase.co`
- Key: `SUPABASE_ANON_KEY` | Value: `eyJhbGciOiJIUzI1...`

### Step 4: Click "Create Web Service"
Render will build and start your service. Once complete, Render will give you a live URL:
👉 **`https://veloceeo-ml-search.onrender.com`**

---

## 🖼️ PART 2: Deploy Image ML Search (`image search`)

### Step 1: Create Second Web Service on Render
1. In Render Dashboard, click **New +** ➔ **Web Service**.
2. Connect the same `veloceeo-ml-backend` GitHub repository.

### Step 2: Configure Service Details
Fill in:

- **Name**: `veloceeo-image-search`
- **Root Directory**: `image search`
- **Runtime**: `Python 3` (or `Docker`)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Instance Type**: Select **Free**

### Step 3: Set Environment Variables
Add:
- Key: `SUPABASE_URL` | Value: `https://cnqukpjrxrtqqrmertuo.supabase.co`
- Key: `SUPABASE_ANON_KEY` | Value: `eyJhbGciOiJIUzI1...`

### Step 4: Click "Create Web Service"
Render will deploy your Image Search service and provide a live URL:
👉 **`https://veloceeo-image-search.onrender.com`**

---

## ⚡ PART 3: Connect Live Render URLs to Supabase Edge Functions

Once both Render services are live, update your **Supabase Edge Functions**:

### 1. Update `search-products-stores` Edge Function
In Supabase Dashboard ➔ Edge Functions ➔ `search-products-stores`:
Set environment variable / line 4 to:
```typescript
const ML_SERVICE_URL = "https://veloceeo-ml-search.onrender.com/predict";
```

### 2. Update `search-by-image` Edge Function
In Supabase Dashboard ➔ Edge Functions ➔ `search-by-image`:
Set environment variable / line 4 to:
```typescript
const IMAGE_ML_SERVICE_URL = "https://veloceeo-image-search.onrender.com/search-image";
```

---

## 🎉 YOUR ENTIRE ML SEARCH BACKEND IS NOW 100% LIVE ON RENDER.COM!
