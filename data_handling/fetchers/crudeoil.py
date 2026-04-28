from datetime import datetime
import requests
from bs4 import BeautifulSoup

from data_handling.utils.fx import convert_currency
from data_handling.utils.format import format_price


CRUDE_SOURCE = "https://oilprice.com/oil-price-charts/#prices"


def fetch_crude_oil_price(rates):
    try:
        # ----------------------------
        # 1. Fetch Page
        # ----------------------------
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        resp = requests.get(CRUDE_SOURCE, headers=headers, timeout=15)

        if resp.status_code != 200:
            return _error(f"HTTP {resp.status_code}")

        # ----------------------------
        # 2. Parse HTML
        # ----------------------------
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.find_all("tr")

        usd_bbl = None

        for row in rows:
            if "Indian Basket" in row.get_text():
                cols = row.find_all("td")
                if len(cols) >= 3:
                    price_text = cols[2].get_text().strip().replace(",", "")
                    usd_bbl = float(price_text)
                    break

        if usd_bbl is None:
            return _error("Price not found")

        # ----------------------------
        # 3. Convert USD → INR (shared FX)
        # ----------------------------
        inr_bbl = convert_currency(usd_bbl, rates, "USD", "INR")

        # ----------------------------
        # 4. Timestamp
        # ----------------------------
        formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ----------------------------
        # 5. Return
        # ----------------------------
        return {
            "commodity": "Crude Oil (Indian Basket)",
            "price_usd": format_price(usd_bbl),
            "price_inr": format_price(inr_bbl),
            "unit": "per barrel",
            "last_updated": formatted_time,
            "source": CRUDE_SOURCE
        }

    except Exception as e:
        return _error(str(e))


# ----------------------------
# Error handler
# ----------------------------
def _error(msg):
    return {
        "commodity": "Crude Oil (Indian Basket)",
        "price_usd": "Error",
        "price_inr": "Error",
        "unit": "",
        "last_updated": f"Failed: {msg}",
        "source": CRUDE_SOURCE
    }