import os
import threading
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

torch.set_num_threads(1)

app = FastAPI(
    title="Veloceeo Live ML Semantic Search Service",
    description="ML-powered vector embedding semantic search API connected to live Supabase database",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cnqukpjrxrtqqrmertuo.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNucXVrcGpyeHJ0cXFybWVydHVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1MzcxMTcsImV4cCI6MjA3NjExMzExN30.uQpavj2QhduGSYmRuqOvKS_H7pUhZVZNPWqqUIzw9_0")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
model = None

class SearchQueryRequest(BaseModel):
    query: str
    top_k_products: Optional[int] = 20
    top_k_stores: Optional[int] = 10

class SearchMLResponse(BaseModel):
    product_ids: List[int]
    store_ids: List[int]

INDEXED_PRODUCTS = []
INDEXED_STORES = []
PRODUCT_EMBEDDINGS = None
STORE_EMBEDDINGS = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

def reload_database_embeddings():
    global INDEXED_PRODUCTS, INDEXED_STORES, PRODUCT_EMBEDDINGS, STORE_EMBEDDINGS
    try:
        m = get_model()
        prod_res = supabase.table("product").select("prod_id, prod_name, prod_description, category, brand").execute()
        INDEXED_PRODUCTS = prod_res.data or []
        
        prod_texts = [
            f"{p.get('prod_name') or ''} {p.get('prod_description') or ''} {p.get('category') or ''} {p.get('brand') or ''}".strip()
            for p in INDEXED_PRODUCTS
        ]
        PRODUCT_EMBEDDINGS = m.encode(prod_texts, normalize_embeddings=True) if prod_texts else np.empty((0, 384))

        store_res = supabase.table("store_details").select("store_id, store_name, store_address, store_district, store_state").execute()
        INDEXED_STORES = store_res.data or []
        
        store_texts = [
            f"{s.get('store_name') or ''} {s.get('store_address') or ''} {s.get('store_district') or ''} {s.get('store_state') or ''}".strip()
            for s in INDEXED_STORES
        ]
        STORE_EMBEDDINGS = m.encode(store_texts, normalize_embeddings=True) if store_texts else np.empty((0, 384))
    except Exception as e:
        print(f"⚠️ Error loading embeddings: {e}")

@app.on_event("startup")
def startup_event():
    threading.Thread(target=reload_database_embeddings, daemon=True).start()

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok", "indexed_products_count": len(INDEXED_PRODUCTS)}

@app.post("/reload")
def reload_index():
    threading.Thread(target=reload_database_embeddings, daemon=True).start()
    return {"status": "reloading_started"}

@app.post("/predict", response_model=SearchMLResponse)
def search_semantic(request: SearchQueryRequest):
    if not request.query or not request.query.strip():
        return SearchMLResponse(product_ids=[], store_ids=[])

    if PRODUCT_EMBEDDINGS is None or PRODUCT_EMBEDDINGS.shape[0] == 0:
        reload_database_embeddings()

    m = get_model()
    query_vector = m.encode(request.query.strip(), normalize_embeddings=True)

    matching_product_ids = []
    if PRODUCT_EMBEDDINGS is not None and PRODUCT_EMBEDDINGS.shape[0] > 0:
        product_scores = np.dot(PRODUCT_EMBEDDINGS, query_vector)
        top_product_indices = np.argsort(product_scores)[::-1][:request.top_k_products]
        
        top_score = product_scores[top_product_indices[0]] if len(top_product_indices) > 0 else 0
        min_threshold = max(0.30, top_score * 0.70)
        
        matching_product_ids = [
            int(INDEXED_PRODUCTS[i]["prod_id"])
            for i in top_product_indices
            if i < len(INDEXED_PRODUCTS) and INDEXED_PRODUCTS[i].get("prod_id") is not None and product_scores[i] >= min_threshold
        ]

    matching_store_ids = []
    if STORE_EMBEDDINGS is not None and STORE_EMBEDDINGS.shape[0] > 0:
        store_scores = np.dot(STORE_EMBEDDINGS, query_vector)
        top_store_indices = np.argsort(store_scores)[::-1][:request.top_k_stores]
        
        top_store_score = store_scores[top_store_indices[0]] if len(top_store_indices) > 0 else 0
        min_store_threshold = max(0.30, top_store_score * 0.70)
        
        matching_store_ids = [
            int(INDEXED_STORES[i]["store_id"])
            for i in top_store_indices
            if i < len(INDEXED_STORES) and INDEXED_STORES[i].get("store_id") is not None and store_scores[i] >= min_store_threshold
        ]

    return SearchMLResponse(product_ids=matching_product_ids, store_ids=matching_store_ids)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
