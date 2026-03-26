from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import logging
import os
from pathlib import Path
import random
import re
import sys
import threading
import time

from bs4 import BeautifulSoup
import requests

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "your_api_key")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
SCRAPE_RETRY_DELAYS_MINUTES = [5, 10, 15]
STEADY_STATE_INTERVAL_MINUTES_RANGE = (13, 17)
STORE_RETRY_DELAYS_SECONDS = [5, 10, 20, 40]
MAX_SCRAPE_ATTEMPTS = 10
PRICE_QUANTIZER = Decimal("0.01")
SUPPLIER_CONFIG_PATH = Path(__file__).with_name("suppliers.json")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }

        event = getattr(record, "event", None)
        if isinstance(event, str):
            payload["event"] = event

        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(fields)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def build_logger():
    logger = logging.getLogger("oil-price-scraper")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


LOGGER = build_logger()


def log_event(level, event, message, **fields):
    LOGGER.log(level, message, extra={"event": event, "fields": fields})


@dataclass(frozen=True)
class SupplierConfig:
    kind: str
    supplier_name: str
    supplier_url: str
    pattern: str | None = None
    class_name: str | None = None
    tag_name: str | None = None
    quantity: int = 150


class OilPrice:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "Connection": "close",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
    }

    def __init__(self, config: SupplierConfig):
        self.config = config
        self.supplier_name = config.supplier_name
        self.supplier_url = config.supplier_url
        self.pattern = re.compile(config.pattern) if config.pattern else None
        self.class_name = config.class_name
        self.tag_name = config.tag_name
        self.quantity = config.quantity

    def fetch_document(self):
        response = requests.get(
            self.supplier_url,
            headers=self.headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def get_prices(self):
        soup = self.fetch_document()
        elements = self.select_elements(soup)
        if not elements:
            raise ValueError(f"No candidate price elements found for {self.supplier_name}")

        prices = self.extract_prices(elements)
        if not prices:
            raise ValueError(f"No prices extracted for {self.supplier_name}")

        deduped_prices = sorted(set(prices), key=lambda item: (item[0], item[1]))
        return {
            "prices": deduped_prices,
            "supplier_name": self.supplier_name,
            "supplier_url": self.supplier_url,
        }

    def select_elements(self, soup):
        if not self.class_name:
            raise ValueError(f"class_name is not configured for {self.supplier_name}")
        return soup.find_all(class_=self.class_name)

    def extract_prices(self, elements):
        raise NotImplementedError


class RegexOilPrice(OilPrice):
    def extract_prices(self, elements):
        prices = []
        for element in elements:
            matches = self.extract_matches(element.get_text(" ", strip=True))
            for quantity, price_text in matches:
                prices.append((int(quantity), parse_price_decimal(price_text)))
        return prices

    def extract_matches(self, text):
        raise NotImplementedError


class DanBell(RegexOilPrice):
    def extract_matches(self, text):
        if self.pattern:
            match = self.pattern.search(text)
            return [(match.group(1), match.group(2))] if match else []
        else:
            return []


class OilPatchFuel(RegexOilPrice):
    def extract_matches(self, text):
        if self.pattern:
            match = self.pattern.search(text)
            return [(match.group(2), match.group(1))] if match else []
        else:
            return []


class AllStateFuel(RegexOilPrice):
    def extract_matches(self, text):
        if self.pattern:
            return self.pattern.findall(text)
        else:
            return []


class OilDepot(OilPrice):
    def select_elements(self, soup):
        if not self.class_name or not self.tag_name:
            raise ValueError("Oil Depot config is missing tag or class selectors")
        price_elements = soup.find_all(self.tag_name, class_=self.class_name)
        if not price_elements:
            return []
        return [price_elements[-1]]

    def extract_prices(self, elements):
        return [(self.quantity, parse_price_decimal(elements[0].get_text(strip=True)))]


class OilExpressFuels(OilPrice):
    PRICE_PATTERN = re.compile(r"\$(\d+(?:\.\d+)?)")

    def extract_prices(self, elements):
        prices = []
        for element in elements:
            text = element.get_text(" ", strip=True)
            match = self.PRICE_PATTERN.search(text)
            if match:
                prices.append((self.quantity, parse_price_decimal(match.group(1))))
        return prices


SUPPLIER_TYPES = {
    "dan_bell": DanBell,
    "oil_patch_fuel": OilPatchFuel,
    "all_state_fuel": AllStateFuel,
    "oil_depot": OilDepot,
    "oil_express_fuels": OilExpressFuels,
}


def parse_price_decimal(raw_value):
    cleaned_value = raw_value.replace("$", "").replace(",", "").replace("*", "").strip()
    try:
        decimal_value = Decimal(cleaned_value)
    except InvalidOperation as error:
        raise ValueError(f"Invalid price value: {raw_value!r}") from error
    return decimal_value.quantize(PRICE_QUANTIZER, rounding=ROUND_HALF_UP)


def load_suppliers():
    with SUPPLIER_CONFIG_PATH.open("r", encoding="utf-8") as config_file:
        supplier_dicts = json.load(config_file)

    suppliers = []
    for supplier_dict in supplier_dicts:
        config = SupplierConfig(**supplier_dict)
        supplier_type = SUPPLIER_TYPES.get(config.kind)
        if supplier_type is None:
            raise ValueError(f"Unsupported supplier type: {config.kind}")
        suppliers.append(supplier_type(config))
    return suppliers


def build_payload(prices, supplier_name, supplier_url):
    payload = []
    for quantity, price in prices:
        if quantity == 150:
            payload.append(
                {
                    "date": datetime.now().date().isoformat(),
                    "price": float(price),
                    "supplier_name": supplier_name,
                    "supplier_url": supplier_url,
                }
            )
    return payload



def store_prices(prices, supplier_name, supplier_url, stop_event: threading.Event):
    payload = build_payload(prices, supplier_name, supplier_url)
    if not payload:
        log_event(
            logging.INFO,
            "store_skipped",
            "No prices matched the storage criteria",
            supplier_name=supplier_name,
            supplier_url=supplier_url,
        )
        return False

    for attempt_number, retry_delay_seconds in enumerate([0] + STORE_RETRY_DELAYS_SECONDS, start=1):
        if retry_delay_seconds > 0:
            stop_event.wait(retry_delay_seconds)

        try:
            response = requests.post(
                f"{API_URL}/prices",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "x-api-key": API_KEY,
                },
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            log_event(
                logging.INFO,
                "store_success",
                "Stored prices successfully",
                supplier_name=supplier_name,
                attempts=attempt_number,
                items=len(payload),
                status_code=response.status_code,
            )
            return True
        except requests.RequestException as error:
            is_last_attempt = attempt_number == len(STORE_RETRY_DELAYS_SECONDS) + 1
            log_level = logging.ERROR if is_last_attempt else logging.WARNING
            log_event(
                log_level,
                "store_failure",
                "Failed to store prices",
                supplier_name=supplier_name,
                attempts=attempt_number,
                items=len(payload),
                error_type=type(error).__name__,
                error=str(error),
                retry_in_seconds=None if is_last_attempt else STORE_RETRY_DELAYS_SECONDS[attempt_number - 1],
            )

    return False


def get_scrape_retry_delay_minutes(attempt_number):
    if attempt_number <= len(SCRAPE_RETRY_DELAYS_MINUTES):
        return SCRAPE_RETRY_DELAYS_MINUTES[attempt_number - 1]
    return random.randint(*STEADY_STATE_INTERVAL_MINUTES_RANGE)


def run_supplier_once(supplier, stop_event):
    scrape_attempt = 1

    while not stop_event.is_set() and scrape_attempt <= MAX_SCRAPE_ATTEMPTS:
        try:
            data = supplier.get_prices()
            stored = store_prices(data["prices"], data["supplier_name"], data["supplier_url"], stop_event)
            if not stored:
                raise RuntimeError(
                    f"Failed to store prices for {supplier.supplier_name} after "
                    f"{len(STORE_RETRY_DELAYS_SECONDS) + 1} attempts"
                )
            log_event(
                logging.INFO,
                "scrape_success",
                "Fetched supplier prices",
                supplier_name=supplier.supplier_name,
                prices_found=data["prices"],
                stored=stored,
            )
            return True
        except Exception as error:
            next_delay_minutes = get_scrape_retry_delay_minutes(scrape_attempt)
            log_event(
                logging.WARNING,
                "scrape_failure",
                "Failed to fetch supplier prices",
                supplier_name=supplier.supplier_name,
                supplier_url=supplier.supplier_url,
                attempts=scrape_attempt,
                error_type=type(error).__name__,
                error=str(error),
                retry_in_minutes=next_delay_minutes,
            )
            scrape_attempt += 1

            if scrape_attempt > MAX_SCRAPE_ATTEMPTS:
                log_event(
                    logging.ERROR,
                    "scrape_exhausted",
                    "Supplier retries exhausted",
                    supplier_name=supplier.supplier_name,
                    supplier_url=supplier.supplier_url,
                    max_attempts=MAX_SCRAPE_ATTEMPTS,
                )
                return False

        if stop_event.wait(next_delay_minutes * 60):
            log_event(
                logging.INFO,
                "worker_stopped",
                "Supplier worker stopped before completion",
                supplier_name=supplier.supplier_name,
            )
            return False

    if stop_event.is_set():
        log_event(
            logging.INFO,
            "worker_stopped",
            "Supplier worker stopped before completion",
            supplier_name=supplier.supplier_name,
        )
        return False

    return False


def main():
    suppliers = load_suppliers()
    stop_event = threading.Event()
    results = {}
    results_lock = threading.Lock()

    def worker(supplier):
        result = run_supplier_once(supplier, stop_event)
        with results_lock:
            results[supplier.supplier_name] = result

    threads: list[threading.Thread] = []

    for supplier in suppliers:
        thread = threading.Thread(
            target=worker,
            args=(supplier,),
            name=f"{supplier.supplier_name}-worker",
        )
        thread.start()
        threads.append(thread)
        log_event(
            logging.INFO,
            "worker_started",
            "Started supplier worker",
            supplier_name=supplier.supplier_name,
        )

    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        log_event(logging.INFO, "shutdown", "Shutdown requested")
        stop_event.set()
        for thread in threads:
            thread.join()

    failed_suppliers = [
        supplier.supplier_name
        for supplier in suppliers
        if not results.get(supplier.supplier_name, False)
    ]

    if failed_suppliers:
        log_event(
            logging.ERROR,
            "job_failed",
            "One or more suppliers failed",
            failed_suppliers=failed_suppliers,
        )
        return 1

    log_event(logging.INFO, "job_succeeded", "All suppliers completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
