from data_handling.utils.sheet_utils import load_sheet, get_sheets_service


def load_commodity_data(sheet_name, spreadsheet_id):
    """
    ML-ready loader (wraps existing sheet_utils)
    """

    service = get_sheets_service()

    df = load_sheet(service, spreadsheet_id, sheet_name)

    if df.empty:
        raise ValueError(f"No data found for {sheet_name}")

    # ----------------------------
    # ML-specific preparation
    # ----------------------------

    # Ensure continuous daily data
    df = df.set_index("date").asfreq("D")

    # Fill missing values (important)
    df["price"] = df["price"].ffill()

    df = df.reset_index()

    return df

