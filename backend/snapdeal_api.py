import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

def fetch_snapdeal_product(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return fallback("Blocked by Snapdeal or Invalid URL")

        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title_tag = soup.find("h1", {"class": "pdp-e-i-head"})
        title = title_tag.get_text(strip=True) if title_tag else "Unavailable"

        # Price
        price_tag = soup.find("span", {"class": "payBlkBig"}) or soup.find("span", {"class": "pdp-final-price"})
        price = (
            price_tag.get_text(strip=True).replace("Rs.", "").replace(",", "").strip()
            if price_tag else "Unavailable"
        )

        # Image
        img_tag = soup.find("img", {"class": "cloudzoom"})
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""
        
        # Sometimes images have a 'lazy-src' or similar, but cloudzoom is usually the main one.
        # Fallback for image
        if not image:
             gallery = soup.select_one("#bx-pager img")
             if gallery and gallery.has_attr("src"):
                 image = gallery["src"]

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Snapdeal Scraper"
        }

    except Exception as e:
        return fallback(str(e))

def fallback(reason):
    return {
        "title": "Unavailable",
        "price": "Unavailable",
        "image": "",
        "source": f"Snapdeal error: {reason}"
    }
