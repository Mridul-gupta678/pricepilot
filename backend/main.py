from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Database
from .database import init_db, save_price, get_price_history

# Scrapers
from .snapdeal_api import fetch_snapdeal_product
from .ajio_api import fetch_ajio_product
from .croma_api import fetch_croma_product

# ===================== APP SETUP =====================

app = FastAPI(title="PricePilot API")

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== MODELS =====================

class ProductPayload(BaseModel):
    url: str
    title: Optional[str] = "Unavailable"
    price: Optional[str] = "Unavailable"
    image: Optional[str] = ""
    source: Optional[str] = "Client Scraper"

# ===================== ROUTES =====================

@app.get("/")
def root():
    return {"status": "PricePilot backend running"}

# ---------- EXISTING ADVANCED COMPARISON ----------

@app.post("/compare-advanced")
def compare_advanced(payload: ProductPayload):
    product = payload.dict()

    if product["price"] not in ["Unavailable", "", None]:
        save_price(product["url"], product["title"], product["price"])

    return product

# ---------- PRICE HISTORY ----------

@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)

# ---------- NEW MULTI-WEBSITE COMPARISON ----------

@app.get("/compare-all")
def compare_all(query: str):
    results = []

    snapdeal = fetch_snapdeal_product(query)
    ajio = fetch_ajio_product(query)
    croma = fetch_croma_product(query)

    results.append(snapdeal)
    results.append(ajio)
    results.append(croma)

    return results
