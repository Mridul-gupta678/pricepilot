import re
import json
import time
import os
from typing import Dict, Optional
from bs4 import BeautifulSoup
import requests

try:
    from curl_cffi import requests as curl_requests
except Exception:
    curl_requests = None

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

USE_IMPERSONATE = True
ENABLE_HEADLESS = True

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _norm_price(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    digits = re.findall(r"\d+", str(text).replace(",", ""))
    return "".join(digits) if digits else None


def _result(source, title=None, price=None, image=None, url=None,
            rating=None, availability=None, seller=None, error=None) -> Dict:
    return {
        "source": source,
        "title": title or "Unavailable",
        "price": price or "Unavailable",
        "image": image or "",
        "url": url or "",
        "rating": rating,
        "availability": availability,
        "seller": seller,
        "error": error,
        "origin": "live",
    }


def _get_html(url: str, referer: str = "", timeout: int = 10) -> str:
    """Fetch HTML — try curl_cffi impersonation first, fall back to requests."""
    if USE_IMPERSONATE and curl_requests:
        try:
            r = curl_requests.get(url, impersonate="chrome124", timeout=timeout)
            if r.status_code == 200 and len(r.text) > 500:
                return r.text
        except Exception:
            pass
    hdrs = {**HEADERS}
    if referer:
        hdrs["Referer"] = referer
    r = requests.get(url, headers=hdrs, timeout=timeout)
    return r.text if r.status_code == 200 else ""


def _headless_html(url: str, wait_for: str = "", timeout_ms: int = 15000) -> Optional[str]:
    """Full Playwright headless fetch — use when normal HTTP is blocked."""
    if not ENABLE_HEADLESS or not sync_playwright:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            ctx = browser.new_context(
                user_agent=UA,
                viewport={"width": 1366, "height": 768},
                locale="en-IN",
            )
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=8000)
                except Exception:
                    pass
            else:
                time.sleep(2)
            html = page.content()
            browser.close()
            return html if len(html) > 500 else None
    except Exception:
        return None


def _jsonld_product(html: str, base_url: str, source: str) -> Optional[Dict]:
    """Extract product data from JSON-LD structured data."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup.find_all("script", {"type": "application/ld+json"}):
            if not tag.string:
                continue
            try:
                data = json.loads(tag.string)
            except Exception:
                continue
            nodes = data if isinstance(data, list) else [data]
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if node.get("@type") == "Product":
                    offers = node.get("offers") or {}
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    price = offers.get("price") or node.get("price")
                    image = node.get("image")
                    if isinstance(image, list):
                        image = image[0] if image else None
                    link = node.get("url") or ""
                    if link.startswith("/"):
                        link = base_url.rstrip("/") + link
                    name = node.get("name")
                    if name:
                        return _result(
                            source,
                            title=name,
                            price=_norm_price(str(price)) if price else None,
                            image=image,
                            url=link,
                            availability="In Stock",
                        )
    except Exception:
        pass
    return None


# ─── Amazon ───────────────────────────────────────────────────────────────────

def search_amazon(query: str) -> Dict:
    url = f"https://www.amazon.in/s?k={requests.utils.quote(query)}&ref=nb_sb_noss"
    try:
        html = _get_html(url, referer="https://www.amazon.in/")
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one("div[data-component-type='s-search-result']")
        if not item:
            # Try headless
            html = _headless_html(url, wait_for="div[data-component-type='s-search-result']") or ""
            soup = BeautifulSoup(html, "html.parser")
            item = soup.select_one("div[data-component-type='s-search-result']")
        if not item:
            return _result("Amazon", error="Blocked or no results")

        title_el = item.select_one("h2 .a-link-normal span") or item.select_one("h2 span")
        price_el = item.select_one(".a-price .a-offscreen") or item.select_one(".a-price-whole")
        img_el = item.select_one("img.s-image")
        link_el = item.select_one("h2 a.a-link-normal")
        rating_el = item.select_one("span.a-icon-alt")

        link = ("https://www.amazon.in" + link_el["href"]) if link_el and link_el.get("href") else ""
        price_raw = price_el.get_text(strip=True) if price_el else None

        return _result(
            "Amazon",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_raw),
            image=img_el.get("src") if img_el else None,
            url=link,
            rating=rating_el.get_text(strip=True).split()[0] if rating_el else None,
            availability="In Stock",
        )
    except Exception as e:
        return _result("Amazon", error=str(e))


# ─── Flipkart ─────────────────────────────────────────────────────────────────

def search_flipkart(query: str) -> Dict:
    url = f"https://www.flipkart.com/search?q={requests.utils.quote(query)}&sort=relevance"
    try:
        html = _get_html(url, referer="https://www.flipkart.com/")
        soup = BeautifulSoup(html, "html.parser")

        # Try JSON-LD first
        jld = _jsonld_product(html, "https://www.flipkart.com", "Flipkart")
        if jld and jld.get("title") != "Unavailable":
            return jld

        # Multiple selector variants Flipkart uses
        item = (
            soup.select_one("a[href*='/p/']") or
            soup.select_one("div._1AtVbE a") or
            soup.select_one("div.tUxRFH") or
            soup.select_one("div._2kHMtA")
        )

        if not item:
            html = _headless_html(url, wait_for="div._1AtVbE") or ""
            soup = BeautifulSoup(html, "html.parser")
            item = (
                soup.select_one("a[href*='/p/']") or
                soup.select_one("div._1AtVbE a")
            )

        if not item:
            return _result("Flipkart", error="No results or JS-blocked")

        title_el = soup.select_one("div._4rR01T") or soup.select_one("a.s1Q9rs") or soup.select_one("div.KzDlHZ")
        price_el = soup.select_one("div._30jeq3") or soup.select_one("div.Nx9bqj")
        img_el = soup.select_one("img._396cs4") or soup.select_one("img._2r_T1I") or soup.select_one("img.DByuf4")
        rating_el = soup.select_one("div._3LWZlK") or soup.select_one("span.Y1HWO0")
        href = item.get("href", "") if hasattr(item, "get") else ""
        link = ("https://www.flipkart.com" + href) if href.startswith("/") else href

        return _result(
            "Flipkart",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=link,
            rating=rating_el.get_text(strip=True) if rating_el else None,
            availability="In Stock",
        )
    except Exception as e:
        return _result("Flipkart", error=str(e))


# ─── Ajio ─────────────────────────────────────────────────────────────────────

def search_ajio(query: str) -> Dict:
    url = f"https://www.ajio.com/search/?text={requests.utils.quote(query)}"
    try:
        # Ajio requires headless — it's a React SPA
        html = _headless_html(url, wait_for=".item", timeout_ms=18000)
        if not html:
            html = _get_html(url, referer="https://www.ajio.com/")

        jld = _jsonld_product(html or "", "https://www.ajio.com", "Ajio")
        if jld and jld.get("title") != "Unavailable":
            return jld

        soup = BeautifulSoup(html or "", "html.parser")
        item = (
            soup.select_one("div.item") or
            soup.select_one("div.preview-inner-container") or
            soup.select_one("li.preview-item")
        )
        if not item:
            return _result("Ajio", error="Login/JS wall")

        title_el = item.select_one(".nameCls") or item.select_one(".name") or item.select_one(".brand")
        price_el = item.select_one(".price") or item.select_one(".final-price") or item.select_one(".priceCol")
        img_el = item.select_one("img")
        link_el = item.select_one("a")
        href = link_el.get("href", "") if link_el else ""
        link = ("https://www.ajio.com" + href) if href.startswith("/") else href

        return _result(
            "Ajio",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=link,
            availability="In Stock",
        )
    except Exception as e:
        return _result("Ajio", error=str(e))


# ─── Snapdeal ─────────────────────────────────────────────────────────────────

def search_snapdeal(query: str) -> Dict:
    url = f"https://www.snapdeal.com/search?keyword={requests.utils.quote(query)}&sort=rlvncy"
    try:
        html = _get_html(url, referer="https://www.snapdeal.com/")
        soup = BeautifulSoup(html, "html.parser")

        item = soup.select_one(".product-tuple-listing") or soup.select_one("li.product-item")
        if not item:
            html = _headless_html(url, wait_for=".product-tuple-listing") or ""
            soup = BeautifulSoup(html, "html.parser")
            item = soup.select_one(".product-tuple-listing") or soup.select_one("li.product-item")

        if not item:
            return _result("Snapdeal", error="No results")

        title_el = item.select_one(".product-title")
        price_el = item.select_one(".product-price") or item.select_one(".lfloat .product-price")
        img_el = item.select_one("img.product-image") or item.select_one("img.product-img")
        link_el = item.select_one("a.dp-widget-link") or item.select_one("a")

        return _result(
            "Snapdeal",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=link_el.get("href") if link_el else None,
            availability="In Stock",
        )
    except Exception as e:
        return _result("Snapdeal", error=str(e))


# ─── Croma ────────────────────────────────────────────────────────────────────

def search_croma(query: str) -> Dict:
    url = f"https://www.croma.com/search/?text={requests.utils.quote(query)}"
    try:
        html = _get_html(url, referer="https://www.croma.com/")
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one("li.product-item") or soup.select_one("div.product-item")

        if not item:
            html = _headless_html(url, wait_for="li.product-item", timeout_ms=18000) or ""
            soup = BeautifulSoup(html, "html.parser")
            item = soup.select_one("li.product-item") or soup.select_one("div.product-item")

        jld = _jsonld_product(html, "https://www.croma.com", "Croma")
        if jld and jld.get("title") != "Unavailable":
            return jld

        if not item:
            return _result("Croma", error="JS-rendered, no data extracted")

        title_el = item.select_one("h3.product-title") or item.select_one("a.product-title") or item.find("h3")
        price_el = (
            item.select_one("span.amount") or
            item.select_one("span.new-price") or
            item.select_one("[class*='price']")
        )
        img_el = item.find("img")
        link_el = item.select_one("a")
        href = link_el.get("href", "") if link_el else ""
        link = ("https://www.croma.com" + href) if href.startswith("/") else href

        return _result(
            "Croma",
            title=title_el.get_text(strip=True) if title_el else None,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=link,
            availability="In Stock",
        )
    except Exception as e:
        return _result("Croma", error=str(e))


# ─── Myntra ───────────────────────────────────────────────────────────────────

def search_myntra(query: str) -> Dict:
    url = f"https://www.myntra.com/{requests.utils.quote(query.replace(' ', '-'))}?rawQuery={requests.utils.quote(query)}"
    try:
        # Myntra is fully React — needs headless
        html = _headless_html(url, wait_for="li.product-base", timeout_ms=18000)
        if not html:
            html = _get_html(url, referer="https://www.myntra.com/")

        soup = BeautifulSoup(html or "", "html.parser")
        item = soup.select_one("li.product-base")

        if not item:
            return _result("Myntra", error="JS-rendered, no results")

        brand_el = item.select_one("h3.product-brand")
        name_el = item.select_one("h4.product-product")
        price_el = item.select_one("span.product-discountedPrice") or item.select_one("span.product-price")
        img_el = item.select_one("img.img-responsive") or item.select_one("img")
        link_el = item.select_one("a")

        title = None
        if brand_el and name_el:
            title = f"{brand_el.get_text(strip=True)} {name_el.get_text(strip=True)}"
        elif name_el:
            title = name_el.get_text(strip=True)
        elif brand_el:
            title = brand_el.get_text(strip=True)

        href = link_el.get("href", "") if link_el else ""
        link = ("https://www.myntra.com/" + href.lstrip("/")) if href and not href.startswith("http") else href

        return _result(
            "Myntra",
            title=title,
            price=_norm_price(price_el.get_text(strip=True) if price_el else None),
            image=img_el.get("src") if img_el else None,
            url=link,
            availability="In Stock",
        )
    except Exception as e:
        return _result("Myntra", error=str(e))
