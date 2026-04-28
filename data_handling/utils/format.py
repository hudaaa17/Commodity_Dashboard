def format_price(value):
    return f"{value:,.2f}" if isinstance(value, (int, float)) else "N/A"