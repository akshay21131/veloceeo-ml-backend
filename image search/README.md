# 🖼️ Veloceeo ML Image-to-Image Visual Search Microservice

A Python FastAPI visual similarity search service powered by OpenAI's **`clip-ViT-B-32`** multimodal model and live Supabase PostgreSQL product image database integration.

---

## 🚀 How to Run Locally

### 1. Navigate to directory
```bash
cd "~/Desktop/Veloceeo/image search"
```

### 2. Install requirements
```bash
pip install -r requirements.txt
```

### 3. Run the Image Search ML service
```bash
python main.py
```
*(Runs on `http://0.0.0.0:8001`)*

---

## 🧪 How to Test Image Search

### Method A: Interactive Swagger API Docs (Browser)
Open: 👉 **[http://localhost:8001/docs](http://localhost:8001/docs)**
- Click `POST /search-image` ➔ `Try it out`
- Upload an image or pass an `image_url` ➔ Click `Execute`.

### Method B: Terminal Curl Request (Image File Upload)
```bash
curl -X POST 'http://localhost:8001/search-image' \
  -F 'file=@/path/to/sample_shirt.jpg'
```

### Method C: Terminal Curl Request (Image URL)
```bash
curl -X POST 'http://localhost:8001/search-image' \
  -F 'image_url=https://example.com/shoe.jpg'
```

Response returned:
```json
{
  "product_ids": [10, 16]
}
```
