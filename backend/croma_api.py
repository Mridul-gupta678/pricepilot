from .search_providers import _get_html, _headless_html, _norm_price, _jsonld_product
from bs4 import BeautifulSoup

def fetch_croma_product(url: str):
    try:
        html = _get_html(url, referer="https://www.croma.com/")
        if len(html) < 2000:
            html = _headless_html(url, wait_for="h1.pd-title") or html
            
        jld = _jsonld_product(html, "https://www.croma.com", "Croma")
        if jld and jld.get("title") != "Unavailable":
            return {
                "title": jld["title"],
                "price": jld["price"],
                "image": jld["image"],
                "source": "Croma Scraper"
            }

        soup = BeautifulSoup(html, "html.parser")
        
        # Product Page selectors
        title_el = soup.select_one("h1.pd-title") or soup.select_one(".product-title")
        title = title_el.get_text(strip=True) if title_el else "Unavailable"
        
        price_el = soup.select_one("#pdp-product-price") or soup.select_one(".amount")
        price = _norm_price(price_el.get_text(strip=True)) if price_el else "Unavailable"
        
        img_el = soup.select_one(".product-img img") or soup.select_one("#pdp-product-image img")
        image = img_el.get("src") if img_el and img_el.get("src") else ""

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Croma Scraper"
        }

    except Exception as e:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": f"Croma error: {e}"
        }
