from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .amazon_api import fetch_amazon_product
from .flipkart_api import fetch_flipkart_product
from .database import init_db, save_price, get_price_history

app = FastAPI(title="PricePilot API")

# ================== INIT DATABASE ==================
init_db()

# ================== CORS ==================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================== ROOT ==================
@app.get("/")
def root():
    return {"status": "PricePilot backend running"}

# ================== COMPARE ADVANCED ==================
@app.post("/compare-advanced")
def compare_advanced(payload: dict):
    url = payload.get("url")

    if not url:
        return {"error": "No URL provided"}

    # 🔍 SOURCE DETECTION
    if "flipkart.com" in url:
        product = fetch_flipkart_product(url)

    elif "amazon." in url:
        product = fetch_amazon_product(url)

    else:
        return {
            "title": "Unsupported website",
            "price": "Unavailable",
            "image": "",
            "source": "Not supported"
        }

    # 💾 SAVE PRICE ONLY IF VALID
    if product.get("price") not in ["Unavailable", None, ""]:
        save_price(url, product.get("title"), product.get("price"))

    return product

# ================== PRICE HISTORY ==================
@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)
