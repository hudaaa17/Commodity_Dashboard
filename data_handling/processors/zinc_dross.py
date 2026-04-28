from data_handling.utils.format import format_price


def compute_zinc_dross(zinc_data, recovery=90):
    try:
        # ----------------------------
        # 1. Validate input
        # ----------------------------
        if not zinc_data or zinc_data.get("price_usd") in ["Error", "N/A"]:
            return _error("No zinc price available")

        # ----------------------------
        # 2. Parse values (remove commas safely)
        # ----------------------------
        usd_price = _parse_price(zinc_data.get("price_usd"))
        inr_price = _parse_price(zinc_data.get("price_inr"))

        if usd_price is None or inr_price is None:
            return _error("Invalid zinc price format")

        # ----------------------------
        # 3. Apply recovery factor
        # ----------------------------
        factor = recovery / 100.0

        dross_usd = usd_price * factor
        dross_inr = inr_price * factor

        # ----------------------------
        # 4. Return
        # ----------------------------
        return {
            "commodity": "Zinc Dross",
            "price_usd": format_price(dross_usd),
            "price_inr": format_price(dross_inr),
            "unit": "per kg",
            "last_updated": zinc_data.get("last_updated"),
            "source": "Derived",
            "deriv": f"Derived from Zinc Metal ({recovery}%)"
        }

    except Exception as e:
        return _error(str(e))


# ----------------------------
# Helpers
# ----------------------------
def _parse_price(value):
    try:
        if not value or value in ["Error", "N/A"]:
            return None
        return float(str(value).replace(",", ""))
    except Exception:
        return None


def _error(msg):
    return {
        "commodity": "Zinc Dross",
        "price_usd": "N/A",
        "price_inr": "N/A",
        "unit": "",
        "last_updated": f"Failed: {msg}",
        "source": "Derived",
        "deriv": ""
    }