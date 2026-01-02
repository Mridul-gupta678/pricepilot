from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import init_db, save_price, get_price_history

app = FastAPI(title="PricePilot API")

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductPayload(BaseModel):
    url: str
    title: str
    price: str
    image: str
    source: str

@app.get("/")
def root():
    return {"status": "PricePilot backend running"}

@app.post("/compare-advanced")
def compare_advanced(payload: ProductPayload):
    if payload.price != "Unavailable":
        save_price(payload.url, payload.title, payload.price)

    return payload

@app.get("/price-history")
def price_history(product_url: str):
    return get_price_history(product_url)
