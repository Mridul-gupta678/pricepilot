from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from urllib.parse import urlparse
import statistics

# Database
from .database import init_db, save_price, get_price_history

# Scrapers
from .amazon_api import fetch_amazon_product
from .flipkart_api import fetch_flipkart_product
from .ajio_api import fetch_ajio_product
from .snapdeal_api import fetch_snapdeal_product
from .scrapers.mock import MockScraper

# Processing
from .processing import DataProcessor

# ===================== APP SETUP =====================

app = FastAPI(title="PricePilot API", version="2.0.0")

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

class ComparisonResponse(BaseModel):
    product: dict
    deal_analysis: dict
    history: List[dict]

# ===================== LOGIC =====================

def scrape_logic(url: str, use_mock: bool = False):
    if use_mock:
        return MockScraper().fetch_product(url)

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
    
    # Normalize Data
    result["title"] = DataProcessor.normalize_title(result.get("title", ""))
    # We keep raw price string for display, but ensure it's not None
    if not result.get("price"):
        result["price"] = "Unavailable"
        
    return result

# ===================== ROUTES =====================

@app.get("/")
def root():
    return {
        "status": "PricePilot backend running",
        "version": "2.0.0",
        "modules": ["Data Collection", "Processing", "Comparison"]
    }

# ---------- ADVANCED COMPARISON ENGINE ----------

@app.post("/compare-advanced", response_model=ComparisonResponse)
def compare_advanced(payload: ProductPayload, mock_mode: bool = False):
    product = payload.dict()

    # 1. Data Collection
    if product["price"] in ["Unavailable", "", None] or mock_mode:
        scraped_data = scrape_logic(product["url"], use_mock=mock_mode)
        product.update(scraped_data)

    # 2. Data Processing & Validation
    current_price_float = DataProcessor.normalize_price(product["price"])
    
    # 3. History & Analysis
    history = get_price_history(product["url"])
    deal_analysis = {
        "score": 0,
        "label": "No Data",
        "savings": 0.0,
        "average_price": 0.0
    }

    if current_price_float:
        # Save valid price
        save_price(product["url"], product["title"], product["price"])
        
        # Calculate Stats
        historical_prices = []
        for entry in history:
            p = DataProcessor.normalize_price(entry["price"])
            if p:
                historical_prices.append(p)
        
        # Include current price in stats if history is empty
        if not historical_prices:
            historical_prices = [current_price_float]
            
        avg_price = statistics.mean(historical_prices)
        
        # 4. Deal Scoring
        deal_metrics = DataProcessor.calculate_deal_score(current_price_float, avg_price)
        deal_analysis.update(deal_metrics)
        deal_analysis["average_price"] = round(avg_price, 2)

    return {
        "product": product,
        "deal_analysis": deal_analysis,
        "history": history
    }

# ---------- UTILITIES ----------

@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)

@app.get("/scrape")
def scrape_product(url: str, mock: bool = False):
    result = scrape_logic(url, use_mock=mock)
    
    # Save if successful
    if result["price"] not in ["Unavailable", "", None]:
        save_price(url, result["title"], result["price"])
        
    return result

@app.get("/health")
def health_check():
    return {"status": "healthy", "services": ["api", "database", "scrapers"]}
