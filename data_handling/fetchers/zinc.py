import os
import requests
from datetime import datetime
from data_handling.utils.format import format_price
from data_handling.utils.fx import convert_currency


ZINC_SOURCE = "https://www.lme.com/metals/non-ferrous/lme-zinc#Summary"
FX_URL = "https://open.er-api.com/v6/latest/USD"


def fetch_zinc_price(rates):
    API_KEY = os.getenv("ZINC_API_KEY")

    # ----------------------------
    # Validate API Key
    # ----------------------------
    if not API_KEY:
        return _error_response("Missing API Key")

    try:
        # ----------------------------
        # 1. Fetch Zinc Price (USD/MT)
        # ----------------------------
        url = f"https://api.metals.dev/v1/metal/spot?api_key={API_KEY}&metal=zinc&currency=USD"

        resp = requests.get(url, timeout=10)

        if resp.status_code != 200:
            return _error_response(f"HTTP {resp.status_code}")

        data = resp.json()

        usd_price_mt = data.get("rate", {}).get("price")
        timestamp = data.get("timestamp")

        if not usd_price_mt or not timestamp:
            return _error_response("Invalid API response")

        # ----------------------------
        # 2. Convert timestamp (UTC → IST)
        # ----------------------------
        dt_utc = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        dt_ist = dt_utc.astimezone()
        formatted_time = dt_ist.strftime("%Y-%m-%d %H:%M:%S")

        # ----------------------------
        # 3. Convert MT → KG
        # ----------------------------

        usd_price_kg = usd_price_mt / 1000


        # ----------------------------
        # 4. Fetch FX rate (USD → INR)
        # ----------------------------

        inr_price_kg = convert_currency(usd_price_kg, rates, "USD", "INR")

        # ----------------------------
        # 5. Format Output
        # ----------------------------
        return {
            "commodity": "Zinc Metal",
            "price_usd": format_price(usd_price_kg),
            "price_inr": format_price(inr_price_kg),
            "unit": "per kg",
            "last_updated": formatted_time,
            "source": ZINC_SOURCE
        }

    except Exception as e:
        return _error_response(str(e))


# ===============================
# 🔧 Helper Functions
# ===============================

def _error_response(msg):
    return {
        "commodity": "Zinc Metal",
        "price_usd": "Error",
        "price_inr": "Error",
        "unit": "",
        "last_updated": msg,
        "source": ZINC_SOURCE
    }