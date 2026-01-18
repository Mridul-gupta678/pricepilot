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


def fetch_myntra_product(url: str):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return {
                "title": "Unavailable",
                "price": "Unavailable",
                "image": "",
                "source": f"Myntra error: HTTP {resp.status_code}",
            }
        soup = BeautifulSoup(resp.text, "html.parser")

        title_el = soup.select_one("h1.pdp-name") or soup.select_one("h1.pdp-title")
        brand_el = soup.select_one("h1.pdp-title") or soup.select_one("h1.pdp-brand")
        full_title = None
        if brand_el and title_el:
            full_title = f"{brand_el.get_text(strip=True)} {title_el.get_text(strip=True)}"
        elif title_el:
            full_title = title_el.get_text(strip=True)
        elif brand_el:
            full_title = brand_el.get_text(strip=True)

        price_el = (
            soup.select_one("span.pdp-price") or
            soup.select_one("span.pdp-discounted-price") or
            soup.select_one("span.pdp-offers-price")
        )
        price = None
        if price_el:
            price = (
                price_el.get_text(strip=True)
                .replace("Rs.", "")
                .replace("₹", "")
                .replace(",", "")
            )

        img_el = soup.select_one("img.pdp-image") or soup.select_one("img[class*='image-image']")
        image = ""
        if img_el:
            image = img_el.get("src") or img_el.get("data-src") or ""

        return {
            "title": full_title or "Unavailable",
            "price": price or "Unavailable",
            "image": image,
            "source": "Myntra Scraper",
        }
    except Exception as e:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": f"Myntra error: {e}",
        }

