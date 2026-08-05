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
import torchvision.models as models
import torchvision.transforms as transforms
from sentence_transformers import SentenceTransformer

torch.set_num_threads(1)

app = FastAPI(
    title="Veloceeo Lightweight ML Microservice",
    description="Combined Text Semantic Search & Vision Image Search API",
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

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "User-Agent": "Mozilla/5.0"
}

text_model = None
vision_model = None
vision_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

class SearchQueryRequest(BaseModel):
    query: str
    top_k_products: Optional[int] = 20
    top_k_stores: Optional[int] = 10

class SearchMLResponse(BaseModel):
    product_ids: List[int]
    store_ids: List[int]

class ImageSearchResponse(BaseModel):
    product_ids: List[int]

INDEXED_PRODUCTS = []
INDEXED_STORES = []
PRODUCT_TEXT_EMBEDDINGS = None
STORE_TEXT_EMBEDDINGS = None

INDEXED_IMAGE_PRODUCTS = []
PRODUCT_IMAGE_EMBEDDINGS = None

def get_text_model():
    global text_model
    if text_model is None:
        text_model = SentenceTransformer("all-MiniLM-L6-v2")
    return text_model

def get_vision_model():
    global vision_model
    if vision_model is None:
        weights = models.MobileNet_V2_Weights.DEFAULT
        m = models.mobilenet_v2(weights=weights)
        m.eval()
        # Extract features before classifier
        vision_model = torch.nn.Sequential(*list(m.children())[:-1])
    return vision_model

def extract_image_features(pil_img: Image.Image) -> np.ndarray:
    try:
        vm = get_vision_model()
        tensor = vision_transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            feat = vm(tensor)
            feat = torch.nn.functional.adaptive_avg_pool2d(feat, (1, 1))
            vec = feat.squeeze().numpy()
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
    except Exception as e:
        print(f"⚠️ Feature extraction error: {e}")
        return np.zeros(1280)

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

def preload_all_embeddings():
    global INDEXED_PRODUCTS, INDEXED_STORES, PRODUCT_TEXT_EMBEDDINGS, STORE_TEXT_EMBEDDINGS
    global INDEXED_IMAGE_PRODUCTS, PRODUCT_IMAGE_EMBEDDINGS
    try:
        print("⚡ Precomputing text & visual embeddings (Ultra-lightweight RAM mode)...")
        tm = get_text_model()

        prod_url = f"{SUPABASE_URL}/rest/v1/product?select=prod_id,prod_name,prod_description,prod_image_urls,category,brand"
        prod_resp = requests.get(prod_url, headers=HEADERS, timeout=10)
        raw_products = prod_resp.json() if prod_resp.status_code == 200 else []
        INDEXED_PRODUCTS = raw_products

        prod_texts = [
            f"{p.get('prod_name') or ''} {p.get('prod_description') or ''} {p.get('category') or ''} {p.get('brand') or ''}".strip()
            for p in raw_products
        ]
        PRODUCT_TEXT_EMBEDDINGS = tm.encode(prod_texts, normalize_embeddings=True) if prod_texts else np.empty((0, 384))

        store_url = f"{SUPABASE_URL}/rest/v1/store_details?select=store_id,store_name,store_address,store_district,store_state"
        store_resp = requests.get(store_url, headers=HEADERS, timeout=10)
        INDEXED_STORES = store_resp.json() if store_resp.status_code == 200 else []
        store_texts = [
            f"{s.get('store_name') or ''} {s.get('store_address') or ''} {s.get('store_district') or ''} {s.get('store_state') or ''}".strip()
            for s in INDEXED_STORES
        ]
        STORE_TEXT_EMBEDDINGS = tm.encode(store_texts, normalize_embeddings=True) if store_texts else np.empty((0, 384))

        indexed_img_prods = []
        img_embeddings_list = []

        for prod in raw_products:
            prod_id = prod.get("prod_id")
            raw_urls = prod.get("prod_image_urls")
            image_urls = parse_image_urls(raw_urls)
            for url in image_urls:
                if not url or not url.startswith("http"):
                    continue
                try:
                    img_resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
                    if img_resp.status_code == 200:
                        img = Image.open(io.BytesIO(img_resp.content)).convert("RGB")
                        img_emb = extract_image_features(img)
                        img_embeddings_list.append(img_emb)
                        indexed_img_prods.append({"prod_id": prod_id, "url": url})
                except Exception as e:
                    print(f"⚠️ Image skip {url}: {e}")

        INDEXED_IMAGE_PRODUCTS = indexed_img_prods
        PRODUCT_IMAGE_EMBEDDINGS = np.array(img_embeddings_list) if img_embeddings_list else np.empty((0, 1280))
        print(f"✅ Loaded {len(INDEXED_PRODUCTS)} products & {len(INDEXED_IMAGE_PRODUCTS)} product images!")
    except Exception as e:
        print(f"⚠️ Preload error: {e}")

@app.on_event("startup")
def startup_event():
    threading.Thread(target=preload_all_embeddings, daemon=True).start()

@app.get("/")
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "indexed_products_count": len(INDEXED_PRODUCTS),
        "indexed_images_count": len(INDEXED_IMAGE_PRODUCTS)
    }

@app.post("/reload")
def reload_index():
    threading.Thread(target=preload_all_embeddings, daemon=True).start()
    return {"status": "reloading_started"}

@app.post("/predict", response_model=SearchMLResponse)
def search_semantic(request: SearchQueryRequest):
    if not request.query or not request.query.strip():
        return SearchMLResponse(product_ids=[], store_ids=[])

    if PRODUCT_TEXT_EMBEDDINGS is None or PRODUCT_TEXT_EMBEDDINGS.shape[0] == 0:
        preload_all_embeddings()

    tm = get_text_model()
    query_vector = tm.encode(request.query.strip(), normalize_embeddings=True)

    matching_product_ids = []
    if PRODUCT_TEXT_EMBEDDINGS is not None and PRODUCT_TEXT_EMBEDDINGS.shape[0] > 0:
        product_scores = np.dot(PRODUCT_TEXT_EMBEDDINGS, query_vector)
        top_product_indices = np.argsort(product_scores)[::-1][:request.top_k_products]
        top_score = product_scores[top_product_indices[0]] if len(top_product_indices) > 0 else 0
        min_threshold = max(0.30, top_score * 0.70)
        matching_product_ids = [
            int(INDEXED_PRODUCTS[i]["prod_id"])
            for i in top_product_indices
            if i < len(INDEXED_PRODUCTS) and INDEXED_PRODUCTS[i].get("prod_id") is not None and product_scores[i] >= min_threshold
        ]

    matching_store_ids = []
    if STORE_TEXT_EMBEDDINGS is not None and STORE_TEXT_EMBEDDINGS.shape[0] > 0:
        store_scores = np.dot(STORE_TEXT_EMBEDDINGS, query_vector)
        top_store_indices = np.argsort(store_scores)[::-1][:request.top_k_stores]
        top_store_score = store_scores[top_store_indices[0]] if len(top_store_indices) > 0 else 0
        min_store_threshold = max(0.30, top_store_score * 0.70)
        matching_store_ids = [
            int(INDEXED_STORES[i]["store_id"])
            for i in top_store_indices
            if i < len(INDEXED_STORES) and INDEXED_STORES[i].get("store_id") is not None and store_scores[i] >= min_store_threshold
        ]

    return SearchMLResponse(product_ids=matching_product_ids, store_ids=matching_store_ids)

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
                target_url = body_json.get("image_url") or body_json.get("imageUrl") or target_url
                target_base64 = body_json.get("image_base64") or body_json.get("imageBase64")
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
        try:
            contents = await file.read()
            query_image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception as e:
            print(f"⚠️ File read error: {e}")

    if not query_image and target_url:
        try:
            resp = requests.get(target_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            if resp.status_code == 200:
                query_image = Image.open(io.BytesIO(resp.content)).convert("RGB")
        except Exception as e:
            print(f"⚠️ Image URL fetch error: {e}")

    if not query_image:
        prod_resp = requests.get(f"{SUPABASE_URL}/rest/v1/product?select=prod_id&limit={top_k}", headers=HEADERS)
        pids = [int(p["prod_id"]) for p in (prod_resp.json() or []) if p.get("prod_id")]
        return ImageSearchResponse(product_ids=pids)

    query_embedding = extract_image_features(query_image)

    if PRODUCT_IMAGE_EMBEDDINGS is None or PRODUCT_IMAGE_EMBEDDINGS.shape[0] == 0:
        prod_resp = requests.get(f"{SUPABASE_URL}/rest/v1/product?select=prod_id&limit={top_k}", headers=HEADERS)
        pids = [int(p["prod_id"]) for p in (prod_resp.json() or []) if p.get("prod_id")]
        return ImageSearchResponse(product_ids=pids)

    scores = np.dot(PRODUCT_IMAGE_EMBEDDINGS, query_embedding)
    top_indices = np.argsort(scores)[::-1]

    seen_prod_ids = set()
    matching_prod_ids = []

    for idx in top_indices:
        pid = INDEXED_IMAGE_PRODUCTS[idx]["prod_id"]
        if pid not in seen_prod_ids:
            seen_prod_ids.add(pid)
            matching_prod_ids.append(int(pid))
            if len(matching_prod_ids) >= top_k:
                break

    return ImageSearchResponse(product_ids=matching_prod_ids)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
