from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ✅ Correct imports (VERY IMPORTANT)
from backend.amazon_api import fetch_amazon_product
from backend.database import init_db, save_price, get_price_history

app = FastAPI(title="PricePilot API")

# Initialize database
init_db()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- MODELS ----------
class ProductURL(BaseModel):
    url: str


# ---------- ROUTES ----------
@app.get("/")
def root():
    return {"status": "PricePilot backend running 🚀"}


@app.post("/compare-advanced")
def compare_advanced(payload: ProductURL):
    url = payload.url

    product = fetch_amazon_product(url)

    # Save price history if price exists
    if product.get("price"):
        save_price(url, product["title"], product["price"])

    return product


@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)
