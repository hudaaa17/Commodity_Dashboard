import pandas as pd

from data_handling.utils.fx import get_all_rates
# ----------------------------
# Fetchers
# ----------------------------
from data_handling.fetchers.zinc import fetch_zinc_price
from data_handling.fetchers.crudepalmoil import fetch_cpo_price
from data_handling.fetchers.brentcrude import fetch_brent_crude_price
from data_handling.fetchers.crudeoil import fetch_crude_oil_price
from data_handling.fetchers.rubber import fetch_rubber_price

# ----------------------------
# Processors
# ----------------------------
from data_handling.processors.zinc_dross import compute_zinc_dross
from data_handling.processors.zinc_oxide import compute_zinc_oxide

# ----------------------------
# Sheet Loader (for ZnO)
# ----------------------------
from data_handling.utils.sheet_utils import load_sheet   


# ----------------------------
# Sheet writer
# ----------------------------

from data_handling.utils.sheet_utils import (
    prepare_sheet_rows,
    update_google_sheets_pipeline
)

# -----------------------
# Adding these as temporary imports
# -----------------------

from dotenv import load_dotenv
load_dotenv()

# -----------------------
# Adding these as temporary variable
# -----------------------



RAW_SPREADSHEET_ID = "1f62apNh7suBrreq_bWE57MvtJFazO_3ZEBTtk9-VBC4"
TRAINING_SPREADSHEET_ID = "1SdojAWIDyX5CEYbUHU5JqjE3iIm-r4mjyWevSmeS0Uc"




def run_webscraping_pipeline():
    """
    Main pipeline:
    - Fetch FX once
    - Fetch all commodity prices
    - Compute derived values
    - Return structured results
    """

    results = []

    # ----------------------------
    # 1. Fetch FX rates ONCE
    # ----------------------------
    try:
        rates = get_all_rates("USD")
    except Exception:
        rates = {}

    # ----------------------------
    # 2. Fetch base commodities
    # ----------------------------
    zinc = fetch_zinc_price(rates)
    cpo = fetch_cpo_price(rates)
    brent = fetch_brent_crude_price(rates)
    crude_indian = fetch_crude_oil_price(rates)
    rubber = fetch_rubber_price()  # no FX needed

    results.extend([zinc, cpo, brent, crude_indian, rubber])

    # ----------------------------
    # 3. Derived: Zinc Dross
    # ----------------------------
    zinc_dross = compute_zinc_dross(zinc)
    results.append(zinc_dross)

    # ----------------------------
    # 4. Derived: Zinc Oxide
    # ----------------------------
    try:
        dross_df = load_sheet("zincdross")  # historical data
        zinc_oxide = compute_zinc_oxide(dross_df, rates)
    except Exception as e:
        zinc_oxide = {
            "commodity": "Zinc Oxide",
            "price_usd": "Error",
            "price_inr": "Error",
            "unit": "",
            "last_updated": f"Failed: {str(e)}",
            "source": "Derived",
            "deriv": ""
        }

    results.append(zinc_oxide)

    # ----------------------------
    # 5. Return final data
    # ----------------------------
    return results


def main():
    # ----------------------------
    # 1. Run pipeline
    # ----------------------------
    data = run_webscraping_pipeline() #--> Returns a list where each element is a dictionary ; commodity wise

    # ----------------------------
    # 2. Convert to sheet rows
    # ----------------------------
    rows = prepare_sheet_rows(data)  #--> Converts dictionary into rows that can be appended in a spreadsheet

    # ----------------------------
    # 3. Update Google Sheets
    # ----------------------------

    # Once we get the rows we update them in the Raw spreadsheet as well as training spreadsheet

    status = update_google_sheets_pipeline(
        rows,
        RAW_SPREADSHEET_ID,
        TRAINING_SPREADSHEET_ID
    )

    print("Pipeline status:", status) # Returns "Sheets updated" or "Today's data exists"

# ----------------------------
# Optional: Run standalone ----This is for testing purpose..
# ----------------------------
if __name__ == "__main__":
    main()