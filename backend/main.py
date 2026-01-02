from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .database import init_db, save_price, get_price_history

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

@app.post("/compare-advanced")
def compare_advanced(payload: ProductPayload):
    product = payload.dict()

    # Save price only if valid
    if product["price"] not in ["Unavailable", "", None]:
        save_price(product["url"], product["title"], product["price"])

    return product

@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)
