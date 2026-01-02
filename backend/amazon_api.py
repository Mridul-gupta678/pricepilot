import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

def fetch_amazon_product(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code != 200:
            return fallback("Blocked by Amazon")

        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title = soup.select_one("#productTitle")
        title = title.get_text(strip=True) if title else "Unavailable"

        # Price (multiple fallbacks)
        price = (
            soup.select_one(".a-price-whole")
            or soup.select_one(".a-offscreen")
        )
        price = price.get_text(strip=True).replace("₹", "") if price else "Unavailable"

        # Image
        image = soup.select_one("#landingImage")
        image = image["src"] if image and image.has_attr("src") else ""

        return {
            "title": title,
            "price": price,
            "image": image,
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
