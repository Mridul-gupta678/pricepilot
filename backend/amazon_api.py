import requests
from bs4 import BeautifulSoup
import json
try:
    from curl_cffi import requests as curl_requests
except Exception:
    curl_requests = None
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Connection": "keep-alive"
}

def _jsonld_pick(soup):
    scripts = soup.find_all("script", {"type": "application/ld+json"})
    for s in scripts:
        if not s.string:
            continue
        try:
            data = json.loads(s.string)
            if isinstance(data, list):
                for d in data:
                    if isinstance(d, dict) and d.get("@type") == "Product":
                        name = d.get("name")
                        offers = d.get("offers") or {}
                        price = offers.get("price") or offers.get("priceSpecification", {}).get("price")
                        image = d.get("image")
                        if isinstance(image, list):
                            image = image[0] if image else ""
                        return name, str(price) if price else None, image
            if isinstance(data, dict) and data.get("@type") == "Product":
                name = data.get("name")
                offers = data.get("offers") or {}
                price = offers.get("price") or offers.get("priceSpecification", {}).get("price")
                image = data.get("image")
                if isinstance(image, list):
                    image = image[0] if image else ""
                return name, str(price) if price else None, image
        except:
            continue
    return None, None, None
def fetch_amazon_product(url: str):
    try:
        parsed = urlparse(url)
        if "amzn" in parsed.netloc:
            try:
                redir = requests.get(url, headers={**HEADERS, "Referer": "https://www.amazon.in/"}, allow_redirects=True, timeout=10)
                url = redir.url or url
            except:
                pass
        html = ""
        if curl_requests:
            r = curl_requests.get(url, impersonate="chrome", timeout=10)
            html = r.text
        else:
            response = requests.get(url, headers={**HEADERS, "Referer": "https://www.amazon.in/"}, timeout=10)
            if response.status_code != 200:
                return fallback("Blocked by Amazon")
            html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title_el = soup.select_one("#productTitle")
        title = title_el.get_text(strip=True) if title_el else None

        # Price (multiple fallbacks)
        price_el = soup.select_one(".a-price-whole") or soup.select_one(".a-offscreen") or soup.select_one("#corePrice_feature_div .a-offscreen")
        price = price_el.get_text(strip=True).replace("₹", "").replace(",", "") if price_el else None

        # Image
        img_el = soup.select_one("#landingImage") or soup.select_one("#imgTagWrapperId img")
        image = img_el["src"] if img_el and img_el.has_attr("src") else ""
        if not title or not price:
            jt, jp, ji = _jsonld_pick(soup)
            title = title or jt or "Unavailable"
            price = price or (jp.replace(",", "") if jp else "Unavailable")
            image = image or (ji or "")
        if not title and not price and not image:
            return fallback("Invalid product URL or blocked")

        return {
            "title": title or "Unavailable",
            "price": price or "Unavailable",
            "image": image or "",
            "source": "Amazon Scraper"
        }

    except Exception as e:
        return fallback(str(e))


def fallback(reason):
    return {
        "title": "Unavailable",
        "price": "Unavailable",
        "image": "",
        "source": f"Amazon blocked ({reason})"
    }

