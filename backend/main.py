from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from amazon_api import fetch_amazon_product
from backend.database import init_db, save_price, get_price_history

app = FastAPI(title="PricePilot API")

# Initialize DB
init_db()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "PricePilot backend running"}

@app.post("/compare-advanced")
def compare_advanced(payload: dict):
    url = payload.get("url")

    if not url:
        return {"error": "No URL provided"}

    product = fetch_amazon_product(url)

    # Save price history if available
    if product.get("price"):
        save_price(url, product["title"], product["price"])

    return product

@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)
