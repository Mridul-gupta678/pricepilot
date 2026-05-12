from .search_providers import _get_html, _headless_html, _norm_price, _jsonld_product
from bs4 import BeautifulSoup
import json

def fetch_myntra_product(url: str):
    try:
        # Myntra is very JS heavy and blocks basic requests
        html = _headless_html(url, wait_for="div.pdp-details", timeout_ms=20000)
        if not html:
            html = _get_html(url, referer="https://www.myntra.com/")
            
        jld = _jsonld_product(html or "", "https://www.myntra.com", "Myntra")
        if jld and jld.get("title") != "Unavailable":
            return {
                "title": jld["title"],
                "price": jld["price"],
                "image": jld["image"],
                "source": "Myntra Scraper"
            }

        soup = BeautifulSoup(html or "", "html.parser")
        
        # PDP selectors
        title_el = soup.select_one("h1.pdp-name")
        brand_el = soup.select_one("h1.pdp-title")
        
        full_title = "Unavailable"
        if brand_el and title_el:
            full_title = f"{brand_el.get_text(strip=True)} {title_el.get_text(strip=True)}"
        elif title_el:
            full_title = title_el.get_text(strip=True)
            
        price_el = soup.select_one("span.pdp-price") or soup.select_one(".pdp-discount")
        price = _norm_price(price_el.get_text(strip=True)) if price_el else "Unavailable"
        
        img_el = soup.select_one("div.image-grid-image") or soup.select_one("img.img-responsive")
        if img_el and img_el.get("style"):
            # Extract background image from style if needed
            import re
            m = re.search(r'url\("(.+?)"\)', img_el["style"])
            image = m.group(1) if m else ""
        else:
            image = img_el.get("src") if img_el and img_el.get("src") else ""

        return {
            "title": full_title,
            "price": price,
            "image": image,
            "source": "Myntra Scraper"
        }

    except Exception as e:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": f"Myntra error: {e}"
        }
