import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_croma_product(query: str):
    url = f"https://www.croma.com/search/?text={query}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        item = soup.select_one(".product-item")
        if not item:
            return {"source": "Croma", "title": "Unavailable"}

        title = item.select_one(".product-title").get_text(strip=True)
        price = item.select_one(".amount").get_text(strip=True).replace("₹", "")
        image = item.find("img")["src"]

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Croma"
        }

    except Exception as e:
        return {"source": "Croma", "error": str(e)}
