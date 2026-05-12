import requests
from bs4 import BeautifulSoup
from .search_providers import _get_html, _headless_html, _norm_price, _jsonld_product

def fetch_flipkart_product(url: str):
    try:
        html = _get_html(url, referer="https://www.flipkart.com/")
        if len(html) < 2000: # Blocked or low content
            html = _headless_html(url, wait_for="span.B_NuCI") or html
            
        jld = _jsonld_product(html, "https://www.flipkart.com", "Flipkart")
        if jld and jld.get("title") != "Unavailable":
            return {
                "title": jld["title"],
                "price": jld["price"],
                "image": jld["image"],
                "source": "Flipkart Scraper"
            }

        soup = BeautifulSoup(html, "html.parser")
        
        # Updated selectors
        title_tag = (
            soup.select_one("span.B_NuCI") or 
            soup.select_one("h1.yhB1nd") or 
            soup.select_one("span.VU-Z7x")
        )
        title = title_tag.get_text(strip=True) if title_tag else "Unavailable"

        price_tag = (
            soup.select_one("div._30jeq3._16Jk6d") or 
            soup.select_one("div.Nx9bqj.C_PkhZ") or 
            soup.select_one("div._30jeq3")
        )
        price = _norm_price(price_tag.get_text(strip=True)) if price_tag else "Unavailable"

        img_tag = (
            soup.select_one("img._396cs4._2amPTt._3qG0Vb") or 
            soup.select_one("img.DByuf4") or 
            soup.select_one("img._396cs4")
        )
        image = img_tag["src"] if img_tag and img_tag.get("src") else ""

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Flipkart Scraper"
        }

    except Exception as e:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": f"Flipkart error: {e}"
        }
