from datetime import datetime
import requests
from bs4 import BeautifulSoup
import boto3
import re
from decimal import Decimal
from boto3.dynamodb.conditions import Key

REGION_NAME = "us-east-2"  # Replace with your region
TABLE_NAME_PRICES = "Oil-Price"
TABLE_NAME_LAST_MODIFIED = "LastModified"

dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME)

def get_last_modified():
    table = dynamodb.Table(TABLE_NAME_LAST_MODIFIED)
    response = table.query(
        KeyConditionExpression=Key('Name').eq('LastModified'),
        Limit=1,
        ScanIndexForward=False
    )
    items = response.get('Items')
    if not items:
        return None, None
    last_item = items[0]
    return last_item.get('If-Modified-Since'), last_item.get('If-None-Match')

def update_last_modified(date, etag):
    table = dynamodb.Table(TABLE_NAME_LAST_MODIFIED)
    table.put_item(
        Item={
            'Name': 'LastModified',
            'Timestamp': datetime.utcnow().isoformat(),
            'If-Modified-Since': date,
            'If-None-Match': etag,
        }
    )

def get_oilexpress_prices():
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
        'Cookie': 'is_mobile=0; language=en'
    }

    supplier_name = "Oil Express Fuels"
    supplier_url = "https://www.oilexpressfuels.com/"
    response = requests.get(supplier_url, headers=headers)

    # Parse the HTML content with Beautiful Soup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Regex pattern to extract the quantity and price
    pattern = re.compile(r'For (\d+) Gallons or More.*?\$ ([\d.]+)')

    # Find all 'h2' elements with class 'wsite-content-title'
    price_elements = soup.find_all('h2', class_='wsite-content-title')

    prices = []
    for elem in price_elements:
        match = pattern.search(elem.text)
        if match:
            quantity = int(match.group(1))
            price = Decimal(match.group(2))
            prices.append((quantity, price))

    return {prices: prices, supplier_name: supplier_name, supplier_url: supplier_url}

def get_danbell_prices():
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Referer": "https://www.bing.com/",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36 Edg/112.0.1722.48",
    }

    date, etag = get_last_modified()
    if date and etag:
        headers["If-Modified-Since"] = date
        headers["If-None-Match"] = etag

    supplier_name = "Dan Bell Oil"  # Adjust as per your supplier's name
    supplier_url = "http://www.danbelloil.com/"  # Adjust as per your supplier's URL

    response = requests.get(supplier_url, headers=headers)
    if response.status_code == 304:
        return None


    soup = BeautifulSoup(response.content, 'html.parser')
    price_elements = soup.find_all('h4', class_='kvtext')
    pattern = re.compile(r'(\d+) gallons or more-\s*\$([\d.]+) per gallon')
    prices = []
    for elem in price_elements:
        match = pattern.search(elem.text)
        if match:
            quantity = int(match.group(1))
            price = Decimal(match.group(2))
            prices.append((quantity, price))
    date = response.headers.get('Last-Modified')
    etag = response.headers.get('ETag')

    return {prices: prices, date: date, etag: etag, supplier_name: supplier_name, supplier_url: supplier_url}

def store_prices(prices, supplier_name, supplier_url):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('OilPrice')

    for index, (quantity, price) in enumerate(prices):
        table.put_item(
            Item={
                'date': datetime.now().isoformat(),  # 'date' is now the primary key
                'quantity': quantity,
                'price': price,
                'supplier_name': supplier_name,
                'supplier_url': supplier_url,
            }
        )


def job():
    data = get_danbell_prices()
    store_prices(data.prices, data.supplier_name, data.supplier_url)
    update_last_modified(data.date, data.etag)
