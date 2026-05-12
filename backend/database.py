import sqlite3
from datetime import datetime

DB_NAME = "price_history.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_url TEXT,
            title TEXT,
            price TEXT,
            date TEXT
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS product_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            external_id TEXT,
            title TEXT,
            price TEXT,
            currency TEXT,
            url TEXT,
            image TEXT,
            category TEXT,
            brand TEXT,
            updated_at TEXT,
            UNIQUE(source, external_id)
        )
    """
    )
    conn.commit()
    conn.close()


def save_price(product_url, title, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO price_history (product_url, title, price, date)
        VALUES (?, ?, ?, ?)
    """,
        (product_url, title, price, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_price_history(product_url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT price, date
        FROM price_history
        WHERE product_url = ?
        ORDER BY date ASC
    """,
        (product_url,),
    )
    rows = cursor.fetchall()
    conn.close()

    history = []
    for price, date in rows:
        clean_price = "".join(ch for ch in price if ch.isdigit())
        if clean_price:
            history.append(
                {
                    "price": int(clean_price),
                    "date": date,
                }
            )

    return history


def bulk_upsert_products(source, products):
    if not products:
        return 0
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    count = 0
    for p in products:
        cursor.execute(
            """
            INSERT INTO product_catalog (
                source,
                external_id,
                title,
                price,
                currency,
                url,
                image,
                category,
                brand,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source, external_id) DO UPDATE SET
                title=excluded.title,
                price=excluded.price,
                currency=excluded.currency,
                url=excluded.url,
                image=excluded.image,
                category=excluded.category,
                brand=excluded.brand,
                updated_at=excluded.updated_at
        """,
            (
                source,
                p.get("external_id"),
                p.get("title"),
                p.get("price"),
                p.get("currency"),
                p.get("url"),
                p.get("image"),
                p.get("category"),
                p.get("brand"),
                now,
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def search_products_by_name(query, limit=10):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    pattern = "%" + query + "%"
    cursor.execute(
        """
        SELECT source,
               external_id,
               title,
               price,
               currency,
               url,
               image,
               category,
               brand,
               updated_at
        FROM product_catalog
        WHERE title LIKE ?
           OR brand LIKE ?
           OR category LIKE ?
        ORDER BY updated_at DESC
        LIMIT 200
    """,
        (pattern, pattern, pattern),
    )
    rows = cursor.fetchall()
    conn.close()
    terms = [t for t in str(query).lower().split() if t]
    scored = []
    for row in rows:
        (
            source,
            external_id,
            title,
            price,
            currency,
            url,
            image,
            category,
            brand,
            updated_at,
        ) = row
        title_l = (title or "").lower()
        brand_l = (brand or "").lower()
        category_l = (category or "").lower()
        score = 0
        for t in terms:
            if t in title_l:
                score += 3
            if t in brand_l:
                score += 4
            if t in category_l:
                score += 2
        scored.append(
            {
                "source": source,
                "external_id": external_id,
                "title": title,
                "price": price,
                "currency": currency,
                "url": url,
                "image": image,
                "category": category,
                "brand": brand,
                "updated_at": updated_at,
                "_score": score,
            }
        )
    scored.sort(key=lambda x: x["_score"], reverse=True)
    result = []
    for item in scored:
        if len(result) >= int(limit):
            break
        item.pop("_score", None)
        result.append(item)
    return result
