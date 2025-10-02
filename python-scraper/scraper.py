from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup
import re
from decimal import Decimal

API_URL = os.getenv("API_URL", "http://localhost:8000")

class OilPrice:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
    }

    def __init__(self, supplier_name, supplier_url, pattern, class_name):
        self.supplier_name = supplier_name
        self.supplier_url = supplier_url
        self.pattern = re.compile(pattern) if pattern else None
        self.class_name = class_name

    def get_prices(self):
        response = requests.get(self.supplier_url, headers=self.headers)
        soup = BeautifulSoup(response.content, "html.parser")
        print(soup)
        price_elements = soup.find_all(class_=self.class_name)
        prices = self.extract_prices(price_elements)
        prices = list(set(prices))
        return {
            "prices": prices,
            "supplier_name": self.supplier_name,
            "supplier_url": self.supplier_url,
        }

    def extract_prices(self, elements):
        raise NotImplementedError


class DanBell(OilPrice):
    def __init__(self):
        super().__init__(
            "Dan Bell Oil",
            "http://www.danbelloil.com/",
            r"(\d+) gallons or more-\s*\$([\d.]+) per gallon",
            "kvtext",
        )

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            if self.pattern != None:
                match = self.pattern.search(elem.text)
                if match:
                    quantity = int(match.group(1))
                    price = Decimal(match.group(2))
                    prices.append((quantity, price))
        return prices

class OilPatchFuel(OilPrice):
    def __init__(self):
        super().__init__(
            "Oil Patch Fuel",
            "https://oilpatchfuel.com/",
            r"\$(\d+\.\d+) per gallon for orders of (\d+) gallons or more\*",
            "et_pb_text_inner",
        )

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            if self.pattern != None:
                match = self.pattern.search(elem.text)
                if match:
                    price = Decimal(match.group(1))
                    quantity = int(match.group(2))
                    prices.append((quantity, price))  # Reversed to (quantity, price)
        return prices


class AllStateFuel(OilPrice):
    def __init__(self):
        super().__init__(
            "Allstate Fuel Oil",
            "https://www.allstatefuel.com/",
            r"(\d+) Gallons or more\s*:?\s*\$([\d.]+)",
            "lh-1 size-20",
        )

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            if self.pattern != None:
                matches = self.pattern.findall(elem.text)
                for match in matches:
                    quantity = int(match[0])
                    price = Decimal(match[1])
                    prices.append((quantity, price))
        return prices


class OilDepot(OilPrice):
    def __init__(self):
        super().__init__("Oil Depot Inc", "https://oildepotinc.com/", None, None)

    def get_prices(self):
        response = requests.get(self.supplier_url, headers=self.headers)
        response_content = response.text
        soup = BeautifulSoup(response_content, "html.parser")
        elements = [soup.find_all("span", class_="et_pb_sum")[-1]]
        print(elements)
        prices = self.extract_prices(elements)
        prices = list(set(prices))
        return {
            "prices": prices,
            "supplier_name": self.supplier_name,
            "supplier_url": self.supplier_url,
        }

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            try:
                eleText: str = elem.text
                prices.append((150, float(eleText[1:])))
            except Exception as e:
                print(f"Failed to parse element: {elem}")
                print(f"Error: {str(e)}")
        return prices


def store_prices(prices, supplier_name, supplier_url):
    payload = []
    for index, (quantity, price) in enumerate(prices):
        if quantity == 150:
            item = {
                "date": datetime.now().date().isoformat(),
                "price": float(price),
                "supplier_name": supplier_name,
                "supplier_url": supplier_url,
            }
            print(f"Storing item {index + 1} of {len(prices)}")
            print(item)
            payload.append(item)
    if payload:
        try:
            resp = requests.post(f"{API_URL}/prices", json=payload)
            resp.raise_for_status()
            print("✅ Successfully stored prices:", resp.text)
        except Exception as e:
            print("❌ Failed to store prices:", e)

if __name__ == "__main__":
    suppliers = [OilDepot()]
    for supplier in suppliers:
        data = supplier.get_prices()
        print("Parsed prices: ", data)
        store_prices(data["prices"], data["supplier_name"], data["supplier_url"])
    print("Done!")
