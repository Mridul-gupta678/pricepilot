import sqlite3
from datetime import datetime

DB_NAME = "price_history.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT,
            title TEXT,
            price TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_price(product_url, title, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO price_history (product_url, title, price, date)
        VALUES (?, ?, ?, ?)
    """, (product_url, title, price, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_price_history(product_url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT price, date
        FROM price_history
        WHERE product_url = ?
        ORDER BY date ASC
    """, (product_url,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for price, date in rows:
        clean_price = ''.join(ch for ch in price if ch.isdigit())
        if clean_price:
            history.append({
                "price": int(clean_price),
                "date": date
            })

    return history
