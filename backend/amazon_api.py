import hashlib
import hmac
import json
import datetime
import requests
from backend.config import (
    AMAZON_ACCESS_KEY,
    AMAZON_SECRET_KEY,
    AMAZON_ASSOCIATE_TAG,
    AMAZON_REGION,
    AMAZON_HOST,
    AMAZON_ENDPOINT
)

SERVICE = "ProductAdvertisingAPI"
ALGORITHM = "AWS4-HMAC-SHA256"


def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(key, date_stamp, region, service):
    k_date = _sign(("AWS4" + key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    return k_signing


def fetch_amazon_product(asin: str):
    """
    Fetch product details from Amazon PA-API using ASIN
    Returns structured product data
    """

    now = datetime.datetime.utcnow()
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    payload = {
        "ItemIds": [asin],
        "Resources": [
            "Images.Primary.Large",
            "ItemInfo.Title",
            "Offers.Listings.Price"
        ],
        "PartnerTag": AMAZON_ASSOCIATE_TAG,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.in"
    }

    payload_json = json.dumps(payload)

    canonical_headers = (
        f"content-encoding:amz-1.0\n"
        f"content-type:application/json; charset=utf-8\n"
        f"host:{AMAZON_HOST}\n"
        f"x-amz-date:{amz_date}\n"
        f"x-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems\n"
    )

    signed_headers = (
        "content-encoding;content-type;host;x-amz-date;x-amz-target"
    )

    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    canonical_request = (
        "POST\n"
        "/paapi5/getitems\n\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )

    credential_scope = f"{date_stamp}/{AMAZON_REGION}/{SERVICE}/aws4_request"

    string_to_sign = (
        f"{ALGORITHM}\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )

    signing_key = _get_signature_key(
        AMAZON_SECRET_KEY,
        date_stamp,
        AMAZON_REGION,
        SERVICE
    )

    signature = hmac.new(
        signing_key,
        string_to_sign.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    authorization_header = (
        f"{ALGORITHM} "
        f"Credential={AMAZON_ACCESS_KEY}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Content-Encoding": "amz-1.0",
        "X-Amz-Date": amz_date,
        "X-Amz-Target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems",
        "Authorization": authorization_header,
        "Host": AMAZON_HOST
    }

    response = requests.post(
        AMAZON_ENDPOINT,
        data=payload_json,
        headers=headers,
        timeout=10
    )

    data = response.json()

    # -------- SAFE PARSING --------
    try:
        item = data["ItemsResult"]["Items"][0]

        title = item["ItemInfo"]["Title"]["DisplayValue"]
        image = item["Images"]["Primary"]["Large"]["URL"]
        price = item["Offers"]["Listings"][0]["Price"]["DisplayAmount"]

        return {
            "title": title,
            "price": price,
            "image": image,
            "source": "Amazon API"
        }

    except Exception:
        return {
            "title": "Unavailable",
            "price": "Unavailable",
            "image": "",
            "source": "Amazon API (no data)"
        }
