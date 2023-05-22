from datetime import datetime
import requests
from bs4 import BeautifulSoup
import boto3
import schedule
import time
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

def get_oil_prices():
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

    response = requests.get("http://www.danbelloil.com/", headers=headers)
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

    return {prices: prices, date: date, etag: etag}

def store_prices(prices):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('OilPrice')

    for index, (quantity, price) in enumerate(prices):
        table.put_item(
            Item={
                'date': datetime.now().isoformat(),  # 'date' is now the primary key
                'quantity': quantity,
                'price': price
            }
        )


def job():
    data = get_oil_prices()
    store_prices(data.prices)
    update_last_modified(data.date, data.etag)

# run job immediately
job()

# # run job every 12 hours
# schedule.every(12).hours.do(job)

# while True:
#     schedule.run_pending()
#     time.sleep(1)
