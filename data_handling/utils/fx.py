import requests


def get_all_rates(base="USD"):
    url = f"https://open.er-api.com/v6/latest/{base}"
    resp = requests.get(url, timeout=10)
    data = resp.json()

    return data.get("rates", {})


def convert_currency(amount, rates, base, target):
    """
    Convert currency using pre-fetched rates
    """
    if amount is None:
        return None

    if base == "USD":
        rate = rates.get(target)
        return amount * rate if rate else None

    if target == "USD":
        rate = rates.get(base)
        return amount / rate if rate else None

    # cross conversion (MYR → INR via USD)
    usd_value = convert_currency(amount, rates, base, "USD")
    return convert_currency(usd_value, rates, "USD", target)


def get_fx_rate(base="USD", target="INR"):
    """
    Fetch exchange rate: base → target
    Example: USD → INR
    """

    try:
        url = f"https://open.er-api.com/v6/latest/{base}"
        resp = requests.get(url, timeout=10)

        if resp.status_code != 200:
            raise ValueError(f"FX API error: {resp.status_code}")

        data = resp.json()

        rate = data.get("rates", {}).get(target)

        if rate is None:
            raise ValueError(f"{target} not found in FX response")

        return rate

    except Exception as e:
        print(f"[FX ERROR] {e}")
        return None