import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

app = FastAPI(
    title="Veloceeo Live ML Semantic Search Service",
    description="ML-powered vector embedding semantic search API connected to live Supabase database",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase Credentials
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://cnqukpjrxrtqqrmertuo.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNucXVrcGpyeHJ0cXFybWVydHVvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjA1MzcxMTcsImV4cCI6MjA3NjExMzExN30.uQpavj2QhduGSYmRuqOvKS_H7pUhZVZNPWqqUIzw9_0")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load sentence transformer model
MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

class SearchQueryRequest(BaseModel):
    query: str
    top_k_products: Optional[int] = 20
    top_k_stores: Optional[int] = 10

class SearchMLResponse(BaseModel):
    product_ids: List[int]
    store_ids: List[int]

# Cache in-memory vectors
INDEXED_PRODUCTS = []
INDEXED_STORES = []
PRODUCT_EMBEDDINGS = None
STORE_EMBEDDINGS = None

def reload_database_embeddings():
    global INDEXED_PRODUCTS, INDEXED_STORES, PRODUCT_EMBEDDINGS, STORE_EMBEDDINGS
    print("🔄 Fetching live products & stores from Supabase PostgreSQL database...")
    
    # 1. Fetch live products (In Python SDK, use .table() instead of reserved keyword .from())
    prod_res = supabase.table("product").select("prod_id, prod_name, prod_description, category, brand").execute()
    INDEXED_PRODUCTS = prod_res.data or []
    
    prod_texts = [
        f"{p.get('prod_name') or ''} {p.get('prod_description') or ''} {p.get('category') or ''} {p.get('brand') or ''}".strip()
        for p in INDEXED_PRODUCTS
    ]
    
    if prod_texts:
        PRODUCT_EMBEDDINGS = model.encode(prod_texts, normalize_embeddings=True)
    else:
        PRODUCT_EMBEDDINGS = np.empty((0, 384))

    # 2. Fetch live stores
    store_res = supabase.table("store_details").select("store_id, store_name, store_address, store_district, store_state").execute()
    INDEXED_STORES = store_res.data or []
    
    store_texts = [
        f"{s.get('store_name') or ''} {s.get('store_address') or ''} {s.get('store_district') or ''} {s.get('store_state') or ''}".strip()
        for s in INDEXED_STORES
    ]
    
    if store_texts:
        STORE_EMBEDDINGS = model.encode(store_texts, normalize_embeddings=True)
    else:
        STORE_EMBEDDINGS = np.empty((0, 384))
        
    print(f"✅ Loaded {len(INDEXED_PRODUCTS)} live products and {len(INDEXED_STORES)} live stores from Supabase!")

@app.on_event("startup")
def startup_event():
    reload_database_embeddings()

def cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    if doc_vecs.shape[0] == 0:
        return np.array([])
    return np.dot(doc_vecs, query_vec)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "live_products_count": len(INDEXED_PRODUCTS),
        "live_stores_count": len(INDEXED_STORES)
    }

@app.post("/reload")
def reload_index():
    reload_database_embeddings()
    return {"status": "reloaded", "products": len(INDEXED_PRODUCTS), "stores": len(INDEXED_STORES)}

@app.post("/predict", response_model=SearchMLResponse)
def search_semantic(request: SearchQueryRequest):
    if not request.query or not request.query.strip():
        return SearchMLResponse(product_ids=[], store_ids=[])

    # 1. Generate query embedding vector
    query_vector = model.encode(request.query.strip(), normalize_embeddings=True)

    matching_product_ids = []
    if PRODUCT_EMBEDDINGS is not None and PRODUCT_EMBEDDINGS.shape[0] > 0:
        product_scores = cosine_similarity(query_vector, PRODUCT_EMBEDDINGS)
        top_product_indices = np.argsort(product_scores)[::-1][:request.top_k_products]
        matching_product_ids = [
            int(INDEXED_PRODUCTS[i]["prod_id"])
            for i in top_product_indices
            if i < len(INDEXED_PRODUCTS) and INDEXED_PRODUCTS[i].get("prod_id") is not None and product_scores[i] > 0.1
        ]

    matching_store_ids = []
    if STORE_EMBEDDINGS is not None and STORE_EMBEDDINGS.shape[0] > 0:
        store_scores = cosine_similarity(query_vector, STORE_EMBEDDINGS)
        top_store_indices = np.argsort(store_scores)[::-1][:request.top_k_stores]
        matching_store_ids = [
            int(INDEXED_STORES[i]["store_id"])
            for i in top_store_indices
            if i < len(INDEXED_STORES) and INDEXED_STORES[i].get("store_id") is not None and store_scores[i] > 0.1
        ]

    return SearchMLResponse(
        product_ids=matching_product_ids,
        store_ids=matching_store_ids
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
