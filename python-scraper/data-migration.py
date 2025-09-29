import os
import json
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000/prices")
JSON_FILE = "data_clean.json"
BATCH_SIZE = 100  # adjust as needed

def chunked(iterable, size):
    """Yield successive chunks from iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]

def push_prices_to_api(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    # convert Decimal to float and strip extra fields like 'gallons'
    payload = [
        {
            "date": item["date"],
            "supplier_name": item["supplier_name"],
            "supplier_url": item["supplier_url"],
            "price": float(item["price"]),
        }
        for item in data
    ]

    for i, batch in enumerate(chunked(payload, BATCH_SIZE), 1):
        print(f"Sending batch {i} of {len(payload)//BATCH_SIZE + 1}")
        try:
            resp = requests.post(API_URL, json=batch)
            resp.raise_for_status()
            print(f"✅ Batch {i} sent successfully")
        except requests.RequestException as e:
            print(f"❌ Failed to send batch {i}:", e)

if __name__ == "__main__":
    push_prices_to_api(JSON_FILE)
