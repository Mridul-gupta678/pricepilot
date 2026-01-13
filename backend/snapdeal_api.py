from curl_cffi import requests
from bs4 import BeautifulSoup

def fetch_snapdeal_product(url: str):
    try:
        # Use curl_cffi to mimic Chrome
        response = requests.get(
            url, 
            impersonate="chrome", 
            timeout=10
        )
        
        if response.status_code != 200:
            return fallback(f"Blocked or Invalid URL (Status: {response.status_code})")

        soup = BeautifulSoup(response.text, "html.parser")

        # Title
        title_tag = soup.find("h1", {"class": "pdp-e-i-head"})
        title = title_tag.get_text(strip=True) if title_tag else "Unavailable"

        # Price
        price_tag = soup.find("span", {"class": "payBlkBig"}) or soup.find("span", {"class": "pdp-final-price"})
        if price_tag:
            price = price_tag.get_text(strip=True).replace("Rs.", "").replace(",", "").strip()
        else:
            # Check for sold out
            sold_out = soup.find(string=lambda text: "sold out" in text.lower() if text else False)
            if sold_out:
                price = "Sold Out"
            else:
                price = "Unavailable"

        # Image
        img_tag = soup.find("img", {"class": "cloudzoom"})
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""
        
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
