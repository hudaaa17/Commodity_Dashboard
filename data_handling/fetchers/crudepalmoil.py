from datetime import datetime
import requests

from data_handling.utils.fx import convert_currency
from data_handling.utils.format import format_price


CPO_SOURCE = "https://bepi.mpob.gov.my/"


def fetch_cpo_price(rates):
    try:
        # ----------------------------
        # 1. Fetch MPOB Data
        # ----------------------------
        url = "https://mpob.gov.my/wp-json/mpob/v1/daily-price"

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        data = resp.json()

        if data.get("status") != "success":
            return _error("Invalid API status")

        # ----------------------------
        # 2. Extract Price (MYR/MT)
        # ----------------------------
        myr_mt = float(data.get("price"))
        data_date = data.get("date", "Unknown Date")

        formatted_time = f"{data_date} (MPOB)"

        # ----------------------------
        # 3. Convert MYR → USD → INR
        # ----------------------------

        usd_mt = convert_currency(myr_mt, rates, "MYR", "USD")
        inr_mt = convert_currency(usd_mt, rates, "USD", "INR")

        # ----------------------------
        # 4. MT → KG
        # ----------------------------
        usd_kg = usd_mt / 1000 if usd_mt else None
        inr_kg = inr_mt / 1000 if inr_mt else None

        # ----------------------------
        # 5. Return formatted
        # ----------------------------
        return {
            "commodity": "Crude Palm Oil",
            "price_usd": format_price(usd_kg),
            "price_inr": format_price(inr_kg),
            "unit": "per kg",
            "last_updated": formatted_time,
            "source": CPO_SOURCE
        }

    except Exception as e:
        return _error(str(e))


# ----------------------------
# Error handler
# ----------------------------
def _error(msg):
    return {
        "commodity": "Crude Palm Oil",
        "price_usd": "Error",
        "price_inr": "Error",
        "unit": "",
        "last_updated": f"Failed: {msg}",
        "source": CPO_SOURCE
    }