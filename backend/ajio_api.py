from curl_cffi import requests
from bs4 import BeautifulSoup
import json
import re

def fetch_ajio_product(url: str):
    # Normalize URL to www.ajio.com to avoid mobile site issues
    url = url.replace("m.ajio.com", "www.ajio.com")
    
    error_msg = ""
    
    # 1. Try fetching the page directly
    try:
        response = requests.get(
            url, 
            impersonate="chrome", 
            timeout=10
        )
        
        if response.status_code == 200:
            return parse_ajio_html(response.text)
        else:
            error_msg = f"Status {response.status_code}"
            
    except Exception as e:
        error_msg = str(e)

    # 2. Fallback: Try API endpoint if main page failed
    # URL format: .../p/{productId}
    match = re.search(r"/p/(\d+)", url)
    if match:
        product_id = match.group(1)
        api_url = f"https://www.ajio.com/api/p/{product_id}"
        try:
            api_response = requests.get(
                api_url,
                headers={
                    "Referer": "https://www.ajio.com/",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                impersonate="chrome",
                timeout=10
            )
            if api_response.status_code == 200:
                data = api_response.json()
                product = data.get("productDetails", {})
                return {
                    "title": product.get("name", "Unavailable"),
                    "price": str(product.get("price", {}).get("value", "Unavailable")),
                    "image": product.get("images", [{}])[0].get("url", ""),
                    "source": "Ajio Scraper (API)"
                }
        except Exception as e:
            error_msg += f" | API Error: {str(e)}"

    return fallback(f"Failed. {error_msg}")

def parse_ajio_html(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Try JSON extraction first (most reliable)
        scripts = soup.find_all("script")
        for script in scripts:
            if script.string and "window.__PRELOADED_STATE__" in script.string:
                try:
                    # Robust extraction
                    content = script.string
                    start_marker = "window.__PRELOADED_STATE__ = "
                    start_index = content.find(start_marker)
                    if start_index != -1:
                        json_text = content[start_index + len(start_marker):]
                        end_index = json_text.find(";")
                        if end_index != -1:
                            json_text = json_text[:end_index]
                        
                        data = json.loads(json_text)
                        product = data.get("product", {}).get("productDetails", {})
                        
                        title = product.get("name", "Unavailable")
                        price = str(product.get("price", {}).get("value", "Unavailable"))
                        images = product.get("images", [])
                        image = images[0].get("url") if images else ""
                        
                        return {
                            "title": title,
                            "price": price,
                            "image": image,
                            "source": "Ajio Scraper"
                        }
                except:
                    pass
        
        # Fallback to HTML selectors
        title_tag = soup.find("h1", {"class": "prod-name"})
        title = title_tag.get_text(strip=True) if title_tag else "Unavailable"
        
        price_tag = soup.find("div", {"class": "prod-sp"})
        price = (
            price_tag.get_text(strip=True).replace("₹", "").replace(",", "")
            if price_tag else "Unavailable"
        )
        
        img_tag = soup.select_one(".img-container img")
        image = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Ajio Scraper (HTML)"
        }

    except Exception as e:
        return fallback(str(e))

def fallback(reason):
    return {
        "title": "Unavailable",
        "price": "Unavailable",
        "image": "",
        "source": f"Ajio error: {reason}"
    }
