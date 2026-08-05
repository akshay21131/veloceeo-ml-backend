import os
import io
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from PIL import Image
import requests
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

app = FastAPI(
    title="Veloceeo ML Image Search Service",
    description="Visual Similarity Search API using CLIP multimodal embeddings for product image search",
    version="1.0.0"
)

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

# Load multimodal CLIP model for visual image search
MODEL_NAME = "clip-ViT-B-32"
model = SentenceTransformer(MODEL_NAME)

class ImageSearchResponse(BaseModel):
    product_ids: List[int]

INDEXED_PRODUCTS = []
PRODUCT_IMAGE_EMBEDDINGS = None

def load_and_embed_product_images():
    global INDEXED_PRODUCTS, PRODUCT_IMAGE_EMBEDDINGS
    print("🖼️ Fetching product image URLs from Supabase PostgreSQL database...")
    
    res = supabase.table("product").select("prod_id, prod_name, prod_image_urls").execute()
    raw_products = res.data or []
    
    INDEXED_PRODUCTS = []
    embeddings_list = []

    for prod in raw_products:
        prod_id = prod.get("prod_id")
        image_urls = prod.get("prod_image_urls") or []
        
        for url in image_urls:
            if not url or not isinstance(url, str):
                continue
            try:
                # Download image and generate CLIP image embedding
                img_resp = requests.get(url, timeout=5)
                if img_resp.status_code == 200:
                    img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                    img_emb = model.encode(img, normalize_embeddings=True)
                    embeddings_list.append(img_emb)
                    INDEXED_PRODUCTS.append({"prod_id": prod_id, "url": url})
            except Exception as e:
                print(f"⚠️ Error embedding image {url}: {e}")

    if embeddings_list:
        PRODUCT_IMAGE_EMBEDDINGS = np.array(embeddings_list)
    else:
        PRODUCT_IMAGE_EMBEDDINGS = np.empty((0, 512))
        
    print(f"✅ Precomputed visual embeddings for {len(INDEXED_PRODUCTS)} product images!")

@app.on_event("startup")
def startup_event():
    load_and_embed_product_images()

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "indexed_images_count": len(INDEXED_PRODUCTS)
    }

@app.post("/reload")
def reload_index():
    load_and_embed_product_images()
    return {"status": "reloaded", "images_count": len(INDEXED_PRODUCTS)}

@app.post("/search-image", response_model=ImageSearchResponse)
async def search_by_image(
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    top_k: int = 10
):
    query_image = None

    if file:
        contents = await file.read()
        query_image = Image.open(io.BytesIO(contents)).convert("RGB")
    elif image_url:
        resp = requests.get(image_url, timeout=5)
        if resp.status_code == 200:
            query_image = Image.open(io.BytesIO(resp.content)).convert("RGB")

    if not query_image:
        raise HTTPException(status_code=400, detail="Please upload an image file or provide an image_url")

    # 1. Encode query image using CLIP model
    query_embedding = model.encode(query_image, normalize_embeddings=True)

    # 2. Cosine similarity against indexed product images
    if PRODUCT_IMAGE_EMBEDDINGS is None or PRODUCT_IMAGE_EMBEDDINGS.shape[0] == 0:
        return ImageSearchResponse(product_ids=[])

    scores = np.dot(PRODUCT_IMAGE_EMBEDDINGS, query_embedding)
    top_indices = np.argsort(scores)[::-1]

    seen_prod_ids = set()
    matching_prod_ids = []

    for idx in top_indices:
        if scores[idx] < 0.2:
            break
        pid = INDEXED_PRODUCTS[idx]["prod_id"]
        if pid not in seen_prod_ids:
            seen_prod_ids.add(pid)
            matching_prod_ids.append(int(pid))
            if len(matching_prod_ids) >= top_k:
                break

    return ImageSearchResponse(product_ids=matching_prod_ids)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
