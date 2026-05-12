from .search_providers import _get_html, _headless_html, _norm_price, _jsonld_product
from bs4 import BeautifulSoup

def fetch_snapdeal_product(url: str):
    try:
        html = _get_html(url, referer="https://www.snapdeal.com/")
        if len(html) < 2000:
            html = _headless_html(url, wait_for="h1.pdp-e-i-head") or html
            
        jld = _jsonld_product(html, "https://www.snapdeal.com", "Snapdeal")
        if jld and jld.get("title") != "Unavailable":
            return {
                "title": jld["title"],
                "price": jld["price"],
                "image": jld["image"],
                "source": "Snapdeal Scraper"
            }

        soup = BeautifulSoup(html, "html.parser")
        
        # PDP selectors
        title_el = soup.select_one("h1.pdp-e-i-head") or soup.select_one(".pdp-product-title")
        title = title_el.get_text(strip=True) if title_el else "Unavailable"
        
        price_el = soup.select_one("span.payBlkBig") or soup.select_one("span.pdp-final-price")
        price = _norm_price(price_el.get_text(strip=True)) if price_el else "Unavailable"
        
        img_el = soup.select_one("img.cloudzoom") or soup.select_one("#bx-pager img")
        image = img_el.get("src") if img_el and img_el.get("src") else ""

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Snapdeal Scraper"
        }

    except Exception as e:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": f"Snapdeal error: {e}"
        }
