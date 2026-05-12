from .search_providers import _get_html, _headless_html, _norm_price, _jsonld_product
from bs4 import BeautifulSoup
import json
import re

def fetch_ajio_product(url: str):
    url = url.replace("m.ajio.com", "www.ajio.com")
    try:
        html = _get_html(url, referer="https://www.ajio.com/")
        if len(html) < 5000:
            html = _headless_html(url, wait_for="div.prod-content") or html
            
        jld = _jsonld_product(html, "https://www.ajio.com", "Ajio")
        if jld and jld.get("title") != "Unavailable":
            return {
                "title": jld["title"],
                "price": jld["price"],
                "image": jld["image"],
                "source": "Ajio Scraper"
            }

        soup = BeautifulSoup(html, "html.parser")
        
        # Try finding preloaded state
        for script in soup.find_all("script"):
            if script.string and "window.__PRELOADED_STATE__" in script.string:
                try:
                    json_text = script.string.split("window.__PRELOADED_STATE__ = ")[1].split(";")[0]
                    data = json.loads(json_text)
                    product = data.get("product", {}).get("productDetails", {})
                    return {
                        "title": product.get("name", "Unavailable"),
                        "price": str(product.get("price", {}).get("value", "Unavailable")),
                        "image": product.get("images", [{}])[0].get("url", ""),
                        "source": "Ajio Scraper"
                    }
                except: pass

        title_tag = soup.select_one("h1.prod-name") or soup.select_one(".brand-name")
        title = title_tag.get_text(strip=True) if title_tag else "Unavailable"
        
        price_tag = soup.select_one(".prod-sp") or soup.select_one(".price-value")
        price = _norm_price(price_tag.get_text(strip=True)) if price_tag else "Unavailable"
        
        img_tag = soup.select_one(".main-img-container img") or soup.select_one(".img-container img")
        image = img_tag["src"] if img_tag and img_tag.get("src") else ""

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Ajio Scraper"
        }

    except Exception as e:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": f"Ajio error: {e}"
        }
