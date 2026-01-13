from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Database
from .database import init_db, save_price, get_price_history
from .amazon_api import fetch_amazon_product
from .flipkart_api import fetch_flipkart_product
from .ajio_api import fetch_ajio_product
from .snapdeal_api import fetch_snapdeal_product
from urllib.parse import urlparse

# Scrapers
# Note: croma_api is available but not integrated into the main logic yet
# from .croma_api import fetch_croma_product 

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

# ===================== LOGIC =====================

def scrape_logic(url: str):
    domain = urlparse(url).netloc.lower()
    
    if "amazon" in domain:
        result = fetch_amazon_product(url)
    elif "flipkart" in domain:
        result = fetch_flipkart_product(url)
    elif "ajio" in domain:
        result = fetch_ajio_product(url)
    elif "snapdeal" in domain:
        result = fetch_snapdeal_product(url)
    else:
        result = {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": "Unsupported Store"
        }
    return result

# ===================== ROUTES =====================

@app.get("/")
def root():
    return {"status": "PricePilot backend running"}

# ---------- EXISTING ADVANCED COMPARISON ----------

@app.post("/compare-advanced")
def compare_advanced(payload: ProductPayload):
    product = payload.dict()

    # If client didn't provide data, try scraping on server
    if product["price"] in ["Unavailable", "", None]:
        scraped_data = scrape_logic(product["url"])
        product.update(scraped_data)

    # Save price only if valid
    if product["price"] not in ["Unavailable", "", None]:
        save_price(product["url"], product["title"], product["price"])

    return product

# ---------- PRICE HISTORY ----------

@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)

@app.get("/scrape")
def scrape_product(url: str):
    result = scrape_logic(url)
    
    # Save if successful
    if result["price"] not in ["Unavailable", "", None]:
        save_price(url, result["title"], result["price"])
        
    return result
