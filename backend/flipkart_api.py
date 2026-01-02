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

def fetch_flipkart_product(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # -------- TITLE --------
        title_tag = soup.find("span", {"class": "B_NuCI"})
        title = title_tag.get_text(strip=True) if title_tag else "Unavailable"

        # -------- PRICE --------
        price_tag = soup.find("div", {"class": "_30jeq3 _16Jk6d"})
        price = (
            price_tag.get_text(strip=True)
            .replace("₹", "")
            .replace(",", "")
            if price_tag else "Unavailable"
        )

        # -------- IMAGE --------
        img_tag = soup.find("img", {"class": "_396cs4"})
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
