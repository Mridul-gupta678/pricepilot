import re
from typing import Dict, Optional
from bs4 import BeautifulSoup
import requests
import json
import time
import os
try:
    from curl_cffi import requests as curl_requests
except Exception:
    curl_requests = None
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
USE_IMPERSONATE = os.getenv("FORCE_IMPERSONATE", "false").lower() in ("1", "true", "yes", "on")
ENABLE_HEADLESS = os.getenv("ENABLE_HEADLESS", "false").lower() in ("1", "true", "yes", "on")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
def _norm_price(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    digits = re.findall(r"\d+", text)
    if not digits:
        return None
    s = "".join(digits)
    return s or None
def _result(source: str, title=None, price=None, image=None, url=None, rating=None, availability=None, seller=None, error=None) -> Dict:
    return {
        "source": source,
        "title": title or "Unavailable",
        "price": price or "Unavailable",
        "image": image or "",
        "url": url or "",
        "rating": rating or None,
        "availability": availability or None,
        "seller": seller or None,
        "error": error or None,
    }
def _jsonld_pick(data) -> Dict:
    try:
        if isinstance(data, list):
            for d in data:
                r = _jsonld_pick(d)
                if r:
                    return r
            return {}
        if isinstance(data, str):
            return _jsonld_pick(json.loads(data))
        t = data.get("@type")
        if t == "ItemList":
            items = data.get("itemListElement") or []
            for it in items:
                if isinstance(it, dict):
                    node = it.get("item") or it.get("@id") or it
                    r = _jsonld_pick(node)
                    if r:
                        return r
            return {}
        if t == "Product":
            name = data.get("name")
            offers = data.get("offers") or {}
            price = offers.get("price") or offers.get("priceSpecification", {}).get("price")
            image = (data.get("image") if isinstance(data.get("image"), str) else (data.get("image") or [None])[0])
            url = data.get("url")
            return {"title": name, "price": _norm_price(str(price) if price else None), "image": image, "url": url}
        name = data.get("name")
        if name and ("offers" in data or "price" in data):
            price = data.get("price") or data.get("offers", {}).get("price")
            image = data.get("image")
            url = data.get("url")
            return {"title": name, "price": _norm_price(str(price) if price else None), "image": image, "url": url}
        return {}
    except:
        return {}
def _try_jsonld(html: str, base: str, source: str) -> Optional[Dict]:
    try:
        soup = BeautifulSoup(html, "html.parser")
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for s in scripts:
            if not s.string:
                continue
            data = json.loads(s.string)
            picked = _jsonld_pick(data)
            if picked and (picked.get("title") or picked.get("price") or picked.get("image")):
                link = picked.get("url")
                if link and link.startswith("/"):
                    link = base + link
                return _result(source, title=picked.get("title"), price=picked.get("price"), image=picked.get("image"), url=link, availability="In Stock")
        return None
    except:
        return None
def _headless_html(url: str, timeout_ms: int = 8000) -> Optional[str]:
    if not ENABLE_HEADLESS or not sync_playwright:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 800})
            page = context.new_page()
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            time.sleep(0.5)
            html = page.content()
            browser.close()
            return html
    except Exception:
        return None
def search_amazon(query: str) -> Dict:
    try:
        url = f"https://www.amazon.in/s?k={requests.utils.quote(query)}"
        html = ""
        for _ in range(2):
            if USE_IMPERSONATE and curl_requests:
                r = curl_requests.get(url, impersonate="chrome", timeout=6)
                html = r.text
            else:
                r = requests.get(url, headers={**HEADERS, "Referer": "https://www.amazon.in/"}, timeout=6)
                html = r.text
            if html:
                break
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one("div.s-result-item[data-component-type='s-search-result']")
        if not item:
            return _result("Amazon", error="No results or blocked")
        title_el = item.select_one("h2 a span")
        price_el = item.select_one(".a-price .a-offscreen")
        img_el = item.select_one("img.s-image")
        link_el = item.select_one("h2 a")
        rating_el = item.select_one("span.a-icon-alt")
        dom_res = _result(
            "Amazon",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=("https://www.amazon.in" + link_el.get("href")) if link_el and link_el.get("href") else None,
            rating=(rating_el.get_text(strip=True).split()[0] if rating_el else None),
            availability="In Stock"
        )
        j = _try_jsonld(html, "https://www.amazon.in", "Amazon")
        if j:
            return _result(
                "Amazon",
                title=(j.get("title") if j.get("title") != "Unavailable" else dom_res.get("title")),
                price=(j.get("price") if j.get("price") != "Unavailable" else dom_res.get("price")),
                image=(j.get("image") or dom_res.get("image")),
                url=(j.get("url") or dom_res.get("url")),
                rating=dom_res.get("rating"),
                availability="In Stock"
            )
        return dom_res
    except Exception as e:
        return _result("Amazon", error=str(e))
def search_flipkart(query: str) -> Dict:
    try:
        url = f"https://www.flipkart.com/search?q={requests.utils.quote(query)}"
        html = ""
        for _ in range(2):
            r = requests.get(url, headers={**HEADERS, "Referer": "https://www.flipkart.com/"}, timeout=6)
            html = r.text
            if html:
                break
        j = _try_jsonld(html, "https://www.flipkart.com", "Flipkart")
        if j:
            return j
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one("a._1fQZEK") or soup.select_one("a.s1Q9rs")
        if not item:
            hhtml = _headless_html(url, timeout_ms=8000)
            if hhtml:
                soup = BeautifulSoup(hhtml, "html.parser")
                item = soup.select_one("a._1fQZEK") or soup.select_one("a.s1Q9rs")
            return _result("Flipkart", error="No results")
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
    except Exception as e:
        return _result("Flipkart", error=str(e))
def search_ajio(query: str) -> Dict:
    try:
        url = f"https://www.ajio.com/search/?text={requests.utils.quote(query)}"
        if USE_IMPERSONATE and curl_requests:
            html = ""
            for _ in range(2):
                r = curl_requests.get(url, impersonate="chrome", timeout=6)
                html = r.text
                if html:
                    break
        else:
            html = ""
            for _ in range(2):
                r = requests.get(url, headers={**HEADERS, "Referer": "https://www.ajio.com/"}, timeout=6)
                html = r.text
                if html:
                    break
        j = _try_jsonld(html, "https://www.ajio.com", "Ajio")
        if j:
            return j
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one("div.item") or soup.select_one(".product-card") or soup.select_one("li")
        if not item:
            hhtml = _headless_html(url, timeout_ms=8000)
            if hhtml:
                soup = BeautifulSoup(hhtml, "html.parser")
                item = soup.select_one("div.item") or soup.select_one(".product-card") or soup.select_one("li")
            return _result("Ajio", error="No results or login required")
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
    except Exception as e:
        return _result("Ajio", error=str(e))
def search_snapdeal(query: str) -> Dict:
    try:
        url = f"https://www.snapdeal.com/search?keyword={requests.utils.quote(query)}"
        if USE_IMPERSONATE and curl_requests:
            html = ""
            for _ in range(2):
                r = curl_requests.get(url, impersonate="chrome", timeout=6)
                html = r.text
                if html:
                    break
        else:
            html = ""
            for _ in range(2):
                r = requests.get(url, headers={**HEADERS, "Referer": "https://www.snapdeal.com/"}, timeout=6)
                html = r.text
                if html:
                    break
        j = _try_jsonld(html, "https://www.snapdeal.com", "Snapdeal")
        if j:
            return j
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one(".product-tuple-listing")
        if not item:
            hhtml = _headless_html(url, timeout_ms=8000)
            if hhtml:
                soup = BeautifulSoup(hhtml, "html.parser")
                item = soup.select_one(".product-tuple-listing")
            return _result("Snapdeal", error="No results")
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
    except Exception as e:
        return _result("Snapdeal", error=str(e))
def search_croma(query: str) -> Dict:
    try:
        url = f"https://www.croma.com/search/?text={requests.utils.quote(query)}"
        html = ""
        for _ in range(2):
            if USE_IMPERSONATE and curl_requests:
                r = curl_requests.get(url, impersonate="chrome", timeout=6)
                html = r.text
            else:
                r = requests.get(url, headers={**HEADERS, "Referer": "https://www.croma.com/"}, timeout=6)
                html = r.text
            if html:
                break
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one(".product-item") or soup.select_one("li.product-item")
        if not item:
            hhtml = _headless_html(url, timeout_ms=8000)
            if hhtml:
                soup = BeautifulSoup(hhtml, "html.parser")
                item = soup.select_one(".product-item") or soup.select_one("li.product-item")
        if not item:
            return _result("Croma", error="No results or JS-rendered")
        title_el = item.select_one(".product-title") or item.find("h3")
        price_el = item.select_one(".amount") or item.select_one(".new-price") or item.find(string=re.compile(r"₹"))
        img_el = item.find("img")
        link_el = item.select_one("a")
        dom_res = _result(
            "Croma",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=(img_el.get("src") if img_el and img_el.get("src") else None),
            url=("https://www.croma.com" + link_el.get("href")) if link_el and link_el.get("href") else None,
            availability="In Stock"
        )
        j = _try_jsonld(html, "https://www.croma.com", "Croma")
        if j:
            return _result(
                "Croma",
                title=(j.get("title") if j.get("title") != "Unavailable" else dom_res.get("title")),
                price=(j.get("price") if j.get("price") != "Unavailable" else dom_res.get("price")),
                image=(j.get("image") or dom_res.get("image")),
                url=(j.get("url") or dom_res.get("url")),
                availability="In Stock"
            )
        return dom_res
    except Exception as e:
        return _result("Croma", error=str(e))
