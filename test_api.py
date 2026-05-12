import requests

r = requests.post(
    "http://127.0.0.1:8000/search-compare",
    json={"name": "boAt Airdopes"},
    timeout=30
)
data = r.json()
results = data.get("results", [])
print(f"Total results: {len(results)}")
for it in results[:10]:
    title = (it.get("title") or "")[:55]
    print(f"  [{it.get('source','?')}] {title} | Price: {it.get('price','?')} | Origin: {it.get('origin','?')}")
