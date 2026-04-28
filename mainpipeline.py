# ----------------------------
# LOAD ENV (IMPORTANT for local + GitHub)
# ----------------------------
from dotenv import load_dotenv
load_dotenv()

# ----------------------------
# IMPORTS
# ----------------------------
from data_handling.pipeline import run_webscraping_pipeline
from data_handling.utils.sheet_utils import (
    prepare_sheet_rows,
    update_google_sheets_pipeline
)

from data_handling.forecast_runner import update_all_forecasts


# ----------------------------
# CONFIG
# ----------------------------
RAW_SPREADSHEET_ID = os.getenv("RAW_SPREADSHEET_ID")
TRAINING_SPREADSHEET_ID = os.getenv("TRAINING_SPREADSHEET_ID")


# ----------------------------
# MAIN PIPELINE
# ----------------------------
def main():

    print("\n🚀 STARTING FULL PIPELINE\n")

    # ----------------------------
    # 1. WEB SCRAPING PIPELINE
    # ----------------------------
    try:
        print("🌐 Running web scraping pipeline...")

        data = run_webscraping_pipeline()

        if not data:
            raise ValueError("No data returned from scraping")

        rows = prepare_sheet_rows(data)

        status = update_google_sheets_pipeline(
            rows,
            RAW_SPREADSHEET_ID,
            TRAINING_SPREADSHEET_ID
        )

        print(f"📊 Data pipeline status: {status}")

    except Exception as e:
        print(f"❌ Web scraping pipeline failed: {e}")
        print("⛔ Stopping pipeline — ML will NOT run")
        return

    # ----------------------------
    # OPTIONAL: Skip ML if no new data
    # ----------------------------
    if status == "exists":
        print("⚠️ No new data → skipping ML forecast step")
        return

    # ----------------------------
    # 2. ML FORECAST PIPELINE
    # ----------------------------
    try:
        print("\n🧠 Running ML forecast pipeline...")

        update_all_forecasts(TRAINING_SPREADSHEET_ID)

        print("📈 Forecasts updated successfully")

    except Exception as e:
        print(f"❌ ML pipeline failed: {e}")

    print("\n✅ FULL PIPELINE COMPLETED\n")


# ----------------------------
# ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    main()
