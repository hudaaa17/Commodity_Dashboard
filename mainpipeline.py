from data_handling.pipeline import run_webscraping_pipeline
from data_handling.utils.sheet_utils import (
    prepare_sheet_rows,
    update_google_sheets_pipeline
)

from ml_pipeline.save_predictions import update_all_forecasts


RAW_SPREADSHEET_ID = "1f62apNh7suBrreq_bWE57MvtJFazO_3ZEBTtk9-VBC4"
TRAINING_SPREADSHEET_ID = "1SdojAWIDyX5CEYbUHU5JqjE3iIm-r4mjyWevSmeS0Uc"


def main():

    print("🚀 STARTING FULL PIPELINE\n")

    # ----------------------------
    # 1. WEB SCRAPING PIPELINE
    # ----------------------------
    try:
        print("🌐 Running web scraping pipeline...")

        data = run_webscraping_pipeline()

        rows = prepare_sheet_rows(data)

        status = update_google_sheets_pipeline(
            rows,
            RAW_SPREADSHEET_ID,
            TRAINING_SPREADSHEET_ID
        )

        print("📊 Data pipeline status:", status)

    except Exception as e:
        print(f"❌ Web scraping pipeline failed: {e}")
        return   # STOP — ML should NOT run without fresh data

    # ----------------------------
    # 2. ML FORECAST PIPELINE
    # ----------------------------
    try:
        print("\n🧠 Running ML forecast pipeline...")

        update_all_forecasts(TRAINING_SPREADSHEET_ID)

        print("📈 Forecasts updated successfully")

    except Exception as e:
        print(f"❌ ML pipeline failed: {e}")

    print("\n✅ FULL PIPELINE COMPLETED")


if __name__ == "__main__":
    main()