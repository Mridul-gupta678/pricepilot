import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
import requests
try:
    from curl_cffi import requests as curl_requests
except Exception:
    curl_requests = None
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.9"}
def _norm_price(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    s = re.sub(r"[^\d.,]", "", text)
    s = s.replace(",", "")
    return s or None
def _result(source: str, title=None, price=None, image=None, url=None, rating=None, availability=None, seller=None) -> Dict:
    return {
        "source": source,
        "title": title or "Unavailable",
        "price": price or "Unavailable",
        "image": image or "",
        "url": url or "",
        "rating": rating or None,
        "availability": availability or None,
        "seller": seller or None,
    }
def search_amazon(query: str) -> Dict:
    try:
        url = f"https://www.amazon.in/s?k={requests.utils.quote(query)}"
        r = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        item = soup.select_one("div.s-result-item[data-component-type='s-search-result']")
        if not item:
            return _result("Amazon")
        title_el = item.select_one("h2 a span")
        price_el = item.select_one(".a-price .a-offscreen")
        img_el = item.select_one("img.s-image")
        link_el = item.select_one("h2 a")
        rating_el = item.select_one("span.a-icon-alt")
        return _result(
            "Amazon",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=("https://www.amazon.in" + link_el.get("href")) if link_el and link_el.get("href") else None,
            rating=(rating_el.get_text(strip=True).split()[0] if rating_el else None),
            availability="In Stock"
        )
    except Exception:
        return _result("Amazon")
def search_flipkart(query: str) -> Dict:
    try:
        url = f"https://www.flipkart.com/search?q={requests.utils.quote(query)}"
        r = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        item = soup.select_one("a._1fQZEK") or soup.select_one("a.s1Q9rs")
        if not item:
            return _result("Flipkart")
        title = item.select_one("div._4rR01T") or item
        price_el = soup.select_one("div._30jeq3._1_WHN1") or soup.select_one("div._30jeq3")
        img_el = soup.select_one("img._396cs4") or soup.select_one("img._2r_T1I")
        rating_el = soup.select_one("div._3LWZlK")
        return _result(
            "Flipkart",
            title=title.get_text(strip=True) if title else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=("https://www.flipkart.com" + item.get("href")) if item.get("href") else None,
            rating=rating_el.get_text(strip=True) if rating_el else None,
            availability="In Stock"
        )
    except Exception:
        return _result("Flipkart")
def search_ajio(query: str) -> Dict:
    try:
        url = f"https://www.ajio.com/search/?text={requests.utils.quote(query)}"
        if curl_requests:
            r = curl_requests.get(url, impersonate="chrome", timeout=5)
            html = r.text
        else:
            r = requests.get(url, headers=HEADERS, timeout=5)
            html = r.text
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one("div.item") or soup.select_one(".product-card") or soup.select_one("li")
        if not item:
            return _result("Ajio")
        title_el = item.select_one(".name") or item.select_one(".brand") or item.find("span")
        price_el = item.select_one(".price") or item.select_one(".final-price") or item.find("span")
        img_el = item.select_one("img")
        link_el = item.select_one("a")
        return _result(
            "Ajio",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=("https://www.ajio.com" + link_el.get("href")) if link_el and link_el.get("href") else None,
            availability="In Stock"
        )
    except Exception:
        return _result("Ajio")
def search_snapdeal(query: str) -> Dict:
    try:
        url = f"https://www.snapdeal.com/search?keyword={requests.utils.quote(query)}"
        if curl_requests:
            r = curl_requests.get(url, impersonate="chrome", timeout=5)
            html = r.text
        else:
            r = requests.get(url, headers=HEADERS, timeout=5)
            html = r.text
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one(".product-tuple-listing")
        if not item:
            return _result("Snapdeal")
        title_el = item.select_one(".product-title") or item.select_one(".product-title-name")
        price_el = item.select_one(".product-price") or item.select_one(".lfloat .product-price")
        img_el = item.select_one("img.product-image")
        link_el = item.select_one("a.dp-widget-link")
        rating_el = item.select_one(".filled-stars")
        return _result(
            "Snapdeal",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=(link_el.get("href") if link_el else None),
            rating=None if not rating_el else rating_el.get("style"),
            availability="In Stock"
        )
    except Exception:
        return _result("Snapdeal")
def search_croma(query: str) -> Dict:
    try:
        url = f"https://www.croma.com/search/?text={requests.utils.quote(query)}"
        r = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        item = soup.select_one(".product-item") or soup.select_one("li.product-item")
        if not item:
            return _result("Croma")
        title_el = item.select_one(".product-title") or item.find("h3")
        price_el = item.select_one(".amount") or item.select_one(".new-price") or item.find(string=re.compile(r"₹"))
        img_el = item.find("img")
        link_el = item.select_one("a")
        return _result(
            "Croma",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=(img_el.get("src") if img_el and img_el.get("src") else None),
            url=("https://www.croma.com" + link_el.get("href")) if link_el and link_el.get("href") else None,
            availability="In Stock"
        )
    except Exception:
        return _result("Croma")
