from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from urllib.parse import urlparse
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import logging
from .search_providers import search_amazon, search_flipkart, search_ajio, search_snapdeal, search_croma
import os
import io
import csv
import json
import xml.etree.ElementTree as ET
import requests

# Database
from .database import init_db, save_price, get_price_history, bulk_upsert_products, search_products_by_name

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
logging.basicConfig(level=logging.INFO)
RUNTIME_FLAGS = {
    "FORCE_IMPERSONATE": os.getenv("FORCE_IMPERSONATE", "false"),
    "ENABLE_HEADLESS": os.getenv("ENABLE_HEADLESS", "false"),
}

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
class SearchPayload(BaseModel):
    name: str
class SearchCompareResponse(BaseModel):
    query: str
    results: List[dict]


class ImportFeedRequest(BaseModel):
    source: str
    url: str
    fmt: Optional[str] = None

# ===================== LOGIC =====================

def scrape_logic(url: str, use_mock: bool = False):
    if use_mock:
        return MockScraper().fetch_product(url)

    domain = urlparse(url).netloc.lower()
    
    if "amazon" in domain or "amzn" in domain:
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

def _guess_feed_format(name: Optional[str], explicit: Optional[str]) -> str:
    if explicit:
        return explicit.lower()
    if not name:
        return "json"
    lower = name.lower()
    if lower.endswith(".csv"):
        return "csv"
    if lower.endswith(".xml") or lower.endswith(".rss"):
        return "xml"
    return "json"


def _parse_csv_feed(data: bytes):
    text = data.decode("utf-8", errors="ignore")
    buf = io.StringIO(text)
    reader = csv.DictReader(buf)
    return [row for row in reader]


def _parse_json_feed(data: bytes):
    text = data.decode("utf-8", errors="ignore")
    obj = json.loads(text)
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ["products", "items", "data"]:
            val = obj.get(key)
            if isinstance(val, list):
                return val
        return [obj]
    return []


def _parse_xml_feed(data: bytes):
    root = ET.fromstring(data)
    items = []
    candidates = []
    for tag in ["item", "product", "offer"]:
        candidates.extend(root.findall(".//" + tag))
    if not candidates:
        candidates = list(root)
    for el in candidates:
        row = {}
        for child in el:
            if child.text is not None:
                row[child.tag] = child.text.strip()
        if row:
            items.append(row)
    return items


def _parse_feed_bytes(data: bytes, fmt: str):
    if fmt == "csv":
        return _parse_csv_feed(data)
    if fmt == "xml":
        return _parse_xml_feed(data)
    return _parse_json_feed(data)


def _pick_field(data: dict, keys):
    for k in keys:
        if k in data and data[k] not in [None, ""]:
            return data[k]
    return None


def _normalize_feed_record(source: str, raw: dict):
    external_id = _pick_field(raw, ["id", "product_id", "item_id", "sku", "offer_id"])
    title = _pick_field(raw, ["title", "name", "product_name", "item_name"])
    if not title:
        return None
    price = _pick_field(raw, ["price", "sale_price", "offer_price", "current_price", "amount"])
    currency = _pick_field(raw, ["currency", "currency_code", "curr"])
    url = _pick_field(raw, ["url", "link", "product_url", "item_url"])
    image = _pick_field(raw, ["image", "image_url", "img", "image_link"])
    category = _pick_field(raw, ["category", "category_name", "cat"])
    brand = _pick_field(raw, ["brand", "brand_name", "manufacturer"])
    normalized_title = DataProcessor.normalize_title(str(title))
    price_value = None
    if price is not None:
        p = DataProcessor.normalize_price(price)
        if p is not None:
            if float(p).is_integer():
                price_value = str(int(p))
            else:
                price_value = str(p)
    return {
        "external_id": str(external_id) if external_id is not None else None,
        "title": normalized_title,
        "price": price_value,
        "currency": currency,
        "url": url,
        "image": image,
        "category": category,
        "brand": brand,
    }


def _feed_rows_to_results(rows):
    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        price_value = row.get("price")
        if price_value is None:
            price_text = "Unavailable"
        else:
            price_text = str(price_value)
        results.append(
            {
                "origin": "feed",
                "source": row.get("source") or "Feed",
                "title": row.get("title") or "Unavailable",
                "price": price_text,
                "image": row.get("image") or "",
                "url": row.get("url") or "",
                "rating": None,
                "availability": "In Stock",
                "seller": row.get("brand"),
                "error": None,
            }
        )
    return results


# ===================== ROUTES =====================
SEARCH_CACHE = {}
CACHE_TTL = 60 * 60 * 24

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
@app.get("/compare-advanced", response_model=ComparisonResponse)
def compare_advanced_get(url: str, mock_mode: bool = False):
    payload = ProductPayload(url=url)
    return compare_advanced(payload, mock_mode=mock_mode)

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
    return {"status": "healthy", "services": ["api", "database", "scrapers"], "runtime_flags": RUNTIME_FLAGS}


@app.post("/admin/import-feed")
async def import_feed(source: str = Form(...), fmt: Optional[str] = Form(None), file: UploadFile = File(...), dry_run: bool = Form(False)):
    resolved_fmt = _guess_feed_format(file.filename, fmt)
    content = await file.read()
    raw_items = _parse_feed_bytes(content, resolved_fmt)
    normalized = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        rec = _normalize_feed_record(source, raw)
        if rec:
            normalized.append(rec)
    if dry_run:
        imported = len(normalized)
    else:
        imported = bulk_upsert_products(source, normalized)
    return {
        "source": source,
        "format": resolved_fmt,
        "total": len(raw_items),
        "imported": imported,
        "dry_run": dry_run,
    }


@app.post("/admin/import-feed-from-url")
def import_feed_from_url(payload: ImportFeedRequest, dry_run: bool = False):
    resolved_fmt = _guess_feed_format(payload.url, payload.fmt)
    try:
        resp = requests.get(payload.url, timeout=30)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch feed: {str(e)}")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Failed to fetch feed")
    raw_items = _parse_feed_bytes(resp.content, resolved_fmt)
    normalized = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        rec = _normalize_feed_record(payload.source, raw)
        if rec:
            normalized.append(rec)
    if dry_run:
        imported = len(normalized)
    else:
        imported = bulk_upsert_products(payload.source, normalized)
    return {
        "source": payload.source,
        "format": resolved_fmt,
        "total": len(raw_items),
        "imported": imported,
        "dry_run": dry_run,
    }


def run_all_search(q: str):
    sites = [
        ("Amazon", search_amazon),
        ("Flipkart", search_flipkart),
        ("Ajio", search_ajio),
        ("Snapdeal", search_snapdeal),
        ("Croma", search_croma),
    ]
    with ThreadPoolExecutor(max_workers=5) as ex:
        future_map = {site: ex.submit(fn, q) for site, fn in sites}
        results = []
        for site, fut in future_map.items():
            try:
                r = fut.result(timeout=6)
                if r:
                    if isinstance(r, dict) and "origin" not in r:
                        r["origin"] = "live"
                    results.append(r)
            except TimeoutError:
                results.append({"origin": "live", "source": site, "title": "Unavailable", "price": "Unavailable", "image": "", "url": "", "error": "Timeout"})
            except Exception as e:
                results.append({"origin": "live", "source": site, "title": "Unavailable", "price": "Unavailable", "image": "", "url": "", "error": str(e)})
        return results
@app.get("/providers-health")
def providers_health(q: str = "iphone"):
    data = run_all_search(q)
    status = []
    for item in data:
        status.append({
            "source": item.get("source"),
            "ok": bool(item.get("title") not in ["Unavailable", None] or item.get("price") not in ["Unavailable", None]),
            "error": item.get("error"),
            "url": item.get("url"),
        })
    return {"query": q, "flags": RUNTIME_FLAGS, "status": status}

def _search_compare_core(q: str):
    key = q.lower()
    now = time.time()
    cached = SEARCH_CACHE.get(key)
    if cached and (now - cached["ts"]) < CACHE_TTL:
        logging.info(f"cache_hit query={q} count={len(cached['data'])}")
        return cached["data"]
    feed_rows = search_products_by_name(q, limit=10)
    feed_results = _feed_rows_to_results(feed_rows)
    live_results = run_all_search(q)
    combined = []
    seen_urls = set()
    for item in feed_results + live_results:
        url = item.get("url") or ""
        key_url = url.lower()
        if key_url:
            if key_url in seen_urls:
                continue
            seen_urls.add(key_url)
        combined.append(item)
    SEARCH_CACHE[key] = {"ts": now, "data": combined}
    logging.info(f"search query={q} count={len(combined)}")
    for item in combined:
        if item.get("price") not in [None, "", "Unavailable", "Sold Out"]:
            save_price(item.get("url", key), item.get("title", q), str(item.get("price")))
    return combined

@app.post("/search-compare", response_model=SearchCompareResponse)
def search_compare(payload: SearchPayload):
    q = payload.name.strip()
    data = _search_compare_core(q)
    return {"query": q, "results": data}

@app.get("/search-compare", response_model=SearchCompareResponse)
def search_compare_get(q: str):
    q = q.strip()
    data = _search_compare_core(q)
    return {"query": q, "results": data}
