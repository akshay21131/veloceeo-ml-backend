import os
import io
import base64
import json
import threading
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
from PIL import Image
import requests
import torch
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

torch.set_num_threads(1)

app = FastAPI(
    title="Veloceeo ML Image Search Service",
    description="Visual Similarity Search API using CLIP multimodal embeddings",
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

class ImageSearchResponse(BaseModel):
    product_ids: List[int]

INDEXED_PRODUCTS = []
PRODUCT_IMAGE_EMBEDDINGS = None

def get_model():
    global model
    if model is None:
        print("⚡ Loading CLIP Vision Model...")
        model = SentenceTransformer("clip-ViT-B-32")
    return model

def parse_image_urls(raw_urls) -> List[str]:
    if not raw_urls:
        return []
    if isinstance(raw_urls, list):
        return [str(u).strip() for u in raw_urls if u and isinstance(u, str)]
    if isinstance(raw_urls, str):
        s = raw_urls.strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(u).strip() for u in parsed if u]
            except Exception:
                cleaned = s.strip("[]\"'").split(",")
                return [c.strip().strip("\"'") for c in cleaned if c.strip()]
        elif s.startswith("http"):
            return [s]
    return []

def load_and_embed_product_images():
    global INDEXED_PRODUCTS, PRODUCT_IMAGE_EMBEDDINGS
    try:
        print("🖼️ Loading product image URLs from Supabase database...")
        m = get_model()
        res = supabase.table("product").select("prod_id, prod_name, prod_image_urls").execute()
        raw_products = res.data or []
        
        indexed_prods = []
        embeddings_list = []

        headers = {"User-Agent": "Mozilla/5.0"}
        for prod in raw_products:
            prod_id = prod.get("prod_id")
            raw_urls = prod.get("prod_image_urls")
            image_urls = parse_image_urls(raw_urls)
            
            for url in image_urls:
                if not url or not url.startswith("http"):
                    continue
                try:
                    img_resp = requests.get(url, headers=headers, timeout=6)
                    if img_resp.status_code == 200:
                        img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                        img_emb = m.encode(img, normalize_embeddings=True)
                        embeddings_list.append(img_emb)
                        indexed_prods.append({"prod_id": prod_id, "url": url})
                        print(f"✅ Indexed image for Product ID {prod_id}: {url}")
                except Exception as e:
                    print(f"⚠️ Error downloading image {url}: {e}")

        INDEXED_PRODUCTS = indexed_prods
        PRODUCT_IMAGE_EMBEDDINGS = np.array(embeddings_list) if embeddings_list else np.empty((0, 512))
        print(f"🎉 Successfully precomputed visual embeddings for {len(INDEXED_PRODUCTS)} product images!")
    except Exception as e:
        print(f"⚠️ Error loading embeddings: {e}")

@app.on_event("startup")
def startup_event():
    threading.Thread(target=load_and_embed_product_images, daemon=True).start()

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "indexed_images_count": len(INDEXED_PRODUCTS),
        "indexed_products": [p["prod_id"] for p in INDEXED_PRODUCTS]
    }

@app.post("/reload")
def reload_index():
    threading.Thread(target=load_and_embed_product_images, daemon=True).start()
    return {"status": "reloading_started"}

@app.post("/search-image", response_model=ImageSearchResponse)
async def search_by_image(
    request: Request,
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    top_k: int = 10
):
    query_image = None
    target_url = image_url
    target_base64 = None

    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body_json = await request.json()
            if isinstance(body_json, dict):
                target_url = body_json.get("image_url") or target_url
                target_base64 = body_json.get("image_base64")
                top_k = body_json.get("top_k") or top_k
        except Exception:
            pass

    if target_base64:
        try:
            clean_b64 = target_base64.split(",")[-1]
            image_bytes = base64.b64decode(clean_b64)
            query_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            print(f"⚠️ Base64 decode error: {e}")

    if not query_image and file:
        contents = await file.read()
        query_image = Image.open(io.BytesIO(contents)).convert("RGB")

    if not query_image and target_url:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(target_url, headers=headers, timeout=6)
        if resp.status_code == 200:
            query_image = Image.open(io.BytesIO(resp.content)).convert("RGB")

    if not query_image:
        res = supabase.table("product").select("prod_id").limit(top_k).execute()
        pids = [int(p["prod_id"]) for p in (res.data or []) if p.get("prod_id")]
        return ImageSearchResponse(product_ids=pids)

    m = get_model()
    query_embedding = m.encode(query_image, normalize_embeddings=True)

    if PRODUCT_IMAGE_EMBEDDINGS is None or PRODUCT_IMAGE_EMBEDDINGS.shape[0] == 0:
        load_and_embed_product_images()

    if PRODUCT_IMAGE_EMBEDDINGS is None or PRODUCT_IMAGE_EMBEDDINGS.shape[0] == 0:
        res = supabase.table("product").select("prod_id").limit(top_k).execute()
        pids = [int(p["prod_id"]) for p in (res.data or []) if p.get("prod_id")]
        return ImageSearchResponse(product_ids=pids)

    # Compute visual cosine similarity matches
    scores = np.dot(PRODUCT_IMAGE_EMBEDDINGS, query_embedding)
    top_indices = np.argsort(scores)[::-1]

    seen_prod_ids = set()
    matching_prod_ids = []

    for idx in top_indices:
        pid = INDEXED_PRODUCTS[idx]["prod_id"]
        if pid not in seen_prod_ids:
            seen_prod_ids.add(pid)
            matching_prod_ids.append(int(pid))
            if len(matching_prod_ids) >= top_k:
                break

    return ImageSearchResponse(product_ids=matching_prod_ids)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
