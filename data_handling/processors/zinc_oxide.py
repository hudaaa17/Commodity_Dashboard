from data_handling.utils.format import format_price
from data_handling.utils.fx import convert_currency
import pandas as pd


INTERCEPT = 113.95466607399345
SLOPE = 0.46424788293579955


def compute_zinc_oxide(dross_df, rates):
    try:
        # ----------------------------
        # 1. Prepare data
        # ----------------------------
        df = dross_df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.dropna(subset=["price"]).sort_values("date")

        # ----------------------------
        # 2. Monthly aggregation
        # ----------------------------
        df["year_month"] = df["date"].dt.to_period("M")
        last_month = df["year_month"].max()

        monthly_avg_usd = df[df["year_month"] == last_month]["price"].mean()

        if not monthly_avg_usd:
            return _error("No valid dross data")

        # ----------------------------
        # 3. Convert USD → INR
        # ----------------------------
        dross_inr = convert_currency(monthly_avg_usd, rates, "USD", "INR")

        # ----------------------------
        # 4. Apply regression
        # ----------------------------
        zno_inr = INTERCEPT + SLOPE * dross_inr

        # ----------------------------
        # 5. Convert back INR → USD
        # ----------------------------
        zno_usd = convert_currency(zno_inr, rates, "INR", "USD")

        # ----------------------------
        # 6. Return
        # ----------------------------
        return {
            "commodity": "Zinc Oxide",
            "price_usd": format_price(zno_usd),
            "price_inr": format_price(zno_inr),
            "unit": "per kg",
            "last_updated": str(last_month),
            "source": "Derived",
            "deriv": "Monthly regression on Zn Dross"
        }

    except Exception as e:
        return _error(str(e))


def _error(msg):
    return {
        "commodity": "Zinc Oxide",
        "price_usd": "Error",
        "price_inr": "Error",
        "unit": "",
        "last_updated": f"Failed: {msg}",
        "source": "Derived",
        "deriv": ""
    }