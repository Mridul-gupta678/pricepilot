import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9",
}

def fetch_flipkart_product(url: str):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # 🔹 TITLE
        title_tag = soup.find("span", class_="VU-ZEz")
        title = title_tag.text.strip() if title_tag else "Unavailable"

        # 🔹 PRICE
        price_tag = soup.find("div", class_="Nx9bqj")
        price = price_tag.text.replace("₹", "").replace(",", "").strip() if price_tag else "Unavailable"

        # 🔹 IMAGE
        img_tag = soup.find("img", class_="_396cs4")
        image = img_tag["src"] if img_tag else ""

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
