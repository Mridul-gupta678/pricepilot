import requests
from bs4 import BeautifulSoup
import json
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

def fetch_ajio_product(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return fallback("Blocked by Ajio or Invalid URL")

        soup = BeautifulSoup(response.text, "html.parser")

        # Ajio is a React app, often data is in a script tag
        # Try to find window.__PRELOADED_STATE__
        script_data = None
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "window.__PRELOADED_STATE__" in script.string:
                try:
                    json_text = script.string.split("window.__PRELOADED_STATE__ = ")[1].split(";")[0]
                    script_data = json.loads(json_text)
                    break
                except:
                    pass
        
        if script_data:
            try:
                product = script_data.get("product", {}).get("productDetails", {})
                title = product.get("name", "Unavailable")
                price = str(product.get("price", {}).get("value", "Unavailable"))
                images = product.get("images", [])
                image = images[0].get("url") if images else ""
                
                return {
                    "title": title,
                    "price": price,
                    "image": image,
                    "source": "Ajio Scraper"
                }
            except:
                pass # Fallback to HTML parsing if JSON structure changed

        # Fallback to HTML parsing
        # Title
        title_tag = soup.find("h1", {"class": "prod-name"})
        title = title_tag.get_text(strip=True) if title_tag else "Unavailable"

        # Price
        price_tag = soup.find("div", {"class": "prod-sp"})
        price = (
            price_tag.get_text(strip=True).replace("₹", "").replace(",", "")
            if price_tag else "Unavailable"
        )

        # Image
        img_tag = soup.select_one(".img-container img")
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Ajio Scraper"
        }

    except Exception as e:
        return fallback(str(e))

def fallback(reason):
    return {
        "title": "Unavailable",
        "price": "Unavailable",
        "image": "",
        "source": f"Ajio error: {reason}"
    }
