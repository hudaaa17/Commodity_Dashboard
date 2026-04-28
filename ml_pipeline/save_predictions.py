import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_handling.utils.sheet_utils import get_sheets_service
from ml_pipeline.pipeline import run_ml_pipeline
from data_handling.utils.fx import get_fx_rate


def compute_zno_forecast(zinc_dross_preds, usd_to_inr):
    INTERCEPT = 113.95466607399345
    SLOPE     = 0.46424788293579955

    # Convert to INR
    dross_inr = [v * usd_to_inr for v in zinc_dross_preds]

    # --- TODAY ---
    zno_today = INTERCEPT + SLOPE * dross_inr[0]

    # --- TARGET ---
    avg_30 = sum(dross_inr[:30]) / len(dross_inr[:30])
    zno_target = INTERCEPT + SLOPE * avg_30

    # --- TREND ---
    diffs = np.diff(dross_inr[:15])
    trend = np.mean(diffs)
    trend = np.clip(trend, -np.std(dross_inr), np.std(dross_inr))

    zno_trend = SLOPE * trend

    days = np.arange(0, 30)

    trend_path = zno_today + zno_trend * days
    target_path = np.linspace(zno_today, zno_target, 30)

    w = (days / 30) ** 2

    forecast_inr = (1 - w) * trend_path + w * target_path

    forecast_usd = forecast_inr / usd_to_inr

    return forecast_usd.tolist()



# Writes an empty sheet with date column
def initialize_forecast_sheet(service, spreadsheet_id, forecast_days=30):
    today = datetime.today().date()

    dates = [
        (today + timedelta(days=i+1)).isoformat()
        for i in range(forecast_days)
    ]

    header = ["Date"]  # only date for now
    values = [header] + [[d] for d in dates]

    # Clear sheet
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range="RecursiveForecast"
    ).execute()

    # Write base structure
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range="RecursiveForecast",
        valueInputOption="RAW",
        body={"values": values}
    ).execute()


def write_forecast_column(
    service,
    spreadsheet_id,
    commodity,
    predictions,
    forecast_days=30,
    sheet_name="RecursiveForecast"
):
    """
    Writes/updates a single commodity column
    """

    # Map commodity → column index
    column_map = {
        "zinc": 1,
        "zincdross":2,
        "zincoxide": 3,
        "rubber": 4,
        "cpo": 5,
        "crudeoil": 6,
        "brentcrude":7 
    }

    col_index = column_map.get(commodity.lower())

    if col_index is None:
        raise ValueError(f"No column mapping for {commodity}")

    # Convert column index → letter
    col_letter = chr(ord('A') + col_index)

    # Prepare values (include header)
    values = [[commodity.capitalize()]] + [
        [float(v)] for v in predictions[:forecast_days]
    ]

    range_str = f"{sheet_name}!{col_letter}1:{col_letter}{forecast_days+1}"

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_str,
        valueInputOption="RAW",
        body={"values": values}
    ).execute()

    print(f"{commodity} forecast written")


def update_all_forecasts(spreadsheet_id):

    service = get_sheets_service()

    # 1. Initialize once
    initialize_forecast_sheet(service, spreadsheet_id)

    base_commodities = ["zinc", "rubber", "cpo", "brentcrude", "crudeoil"]

    results_map = {}

    for c in base_commodities:
            try:
                result = run_ml_pipeline(c, spreadsheet_id)

                preds = result["combined_forecast"]

                results_map[c] = preds

                print(f"✔ {c} success")

            except ValueError as e:
                print(f"⚠️ Skipping {c}: {e}")
                continue

            except Exception as e:
                print(f"❌ Unexpected error in {c}: {e}")
                continue

    if "zinc" in results_map:

            zinc_preds = results_map["zinc"]

            zinc_dross_preds = [0.9 * v for v in zinc_preds]
            results_map["zincdross"] = zinc_dross_preds

            usd_to_inr = get_fx_rate("USD", "INR")

            if usd_to_inr:
                zno_preds = compute_zno_forecast(
                    zinc_dross_preds,
                    usd_to_inr
                )
                results_map["zincoxide"] = zno_preds

    else:
            print("⚠️ Zinc missing → skipping dross & ZnO")

    

    for commodity, preds in results_map.items():
        try:
            write_forecast_column(
                service,
                spreadsheet_id,
                commodity=commodity,
                predictions=preds
            )
            print(f"📊 Written {commodity}")

        except Exception as e:
            print(f"❌ Failed writing {commodity}: {e}")

    print("✅ Forecast update complete")
       
    