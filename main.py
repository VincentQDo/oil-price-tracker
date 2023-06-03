from datetime import datetime
import requests
from bs4 import BeautifulSoup
import boto3
import re
from decimal import Decimal

class OilPrice:
    dynamodb = boto3.resource('dynamodb', region_name="us-east-2")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
    }

    def __init__(self, supplier_name, supplier_url, pattern, class_name):
        self.supplier_name = supplier_name
        self.supplier_url = supplier_url
        self.pattern = re.compile(pattern) if pattern else None
        self.class_name = class_name

    def get_prices(self):
        response = requests.get(self.supplier_url, headers=self.headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        price_elements = soup.find_all(class_=self.class_name)
        prices = self.extract_prices(price_elements)
        prices = list(set(prices))
        return {"prices": prices, "supplier_name": self.supplier_name, "supplier_url": self.supplier_url}
        
    def extract_prices(self, elements):
        raise NotImplementedError

class DanBell(OilPrice):
    def __init__(self):
        super().__init__("Dan Bell Oil", "http://www.danbelloil.com/", r'(\d+) gallons or more-\s*\$([\d.]+) per gallon', 'kvtext')

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            match = self.pattern.search(elem.text)
            if match:
                quantity = int(match.group(1))
                price = Decimal(match.group(2))
                prices.append((quantity, price))
        return prices
    
class OilExpress(OilPrice):
    def __init__(self):
        super().__init__("Oil Express Fuels", "https://www.oilexpressfuels.com/", r'\$ ([\d.]+).*For (\d+) Gallons', 'wsite-content-title')

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            match = self.pattern.search(elem.text)
            if match:
                price = Decimal(match.group(1))
                quantity = int(match.group(2))  # Parse the quantity from the match
                prices.append((quantity, price))
        return prices

class OilPatchFuel(OilPrice):
    def __init__(self):
        super().__init__("Oil Patch Fuel", "https://oilpatchfuel.com/", r'Prices as low as \$([\d.]+) per gallon for online orders of (\d+) gallons or more\*', 'et_pb_text_inner')

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            match = self.pattern.search(elem.text)
            if match:
                price = Decimal(match.group(1))
                quantity = int(match.group(2))
                prices.append((quantity, price))  # Reversed to (quantity, price)
        return prices

class AllStateFuel(OilPrice):
    def __init__(self):
        super().__init__("Allstate Fuel Oil", "https://www.allstatefuel.com/", r'(\d+) Gallons or more\s*:?\s*\$([\d.]+)', 'lh-1 size-20')

    def extract_prices(self, elements):
        prices = []
        for elem in elements:
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
        soup = BeautifulSoup(response.content, 'html.parser')
        elements = soup.find_all(class_=lambda x: x and x.startswith('et_pb_pricing_table et_pb_pricing_table_'))
        prices = self.extract_prices(elements)
        prices = list(set(prices))
        return {"prices": prices, "supplier_name": self.supplier_name, "supplier_url": self.supplier_url}
    
    def extract_prices(self, elements):
        prices = []
        for elem in elements:
            try:
                title = elem.find(class_='et_pb_pricing_title').text
                price_info = elem.find(class_='et_pb_et_price').text.strip()
                quantity_match = re.search(r'(\d+)', title)
                price_match = re.search(r'\$\*?([0-9.]+)', price_info)  # adjusted regex to match optional *
                if quantity_match and price_match:
                    quantity = int(quantity_match.group(1))
                    price = Decimal(price_match.group(1).replace(',', ''))
                    if quantity != 150:
                        price = price / quantity
                    prices.append((quantity, price))
            except Exception as e:
                print(f"Failed to parse element: {elem}")
                print(f"Error: {str(e)}")
        return prices

def store_prices(prices, supplier_name, supplier_url):
    table = OilPrice.dynamodb.Table('Oil-Price')
    for index, (quantity, price) in enumerate(prices):
        table.put_item(
            Item={
                'date': datetime.now().isoformat(),
                'gallons': quantity,
                'price': price,
                'supplier_name': supplier_name,
                'supplier_url': supplier_url,
            }
        )

def job():
    suppliers = [OilExpress(), DanBell(), AllStateFuel(), OilPatchFuel(), OilDepot()]
    for supplier in suppliers:
        data = supplier.get_prices()
        print('Parsed prices: ', data)
        print('Storing prices in DynamoDB...')
        store_prices(data['prices'], data['supplier_name'], data['supplier_url'])
    print('Done!')


job()
