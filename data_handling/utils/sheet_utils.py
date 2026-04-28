
from dotenv import load_dotenv
load_dotenv()

import os
import json
import pandas as pd
import numpy as np
from datetime import date
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


def get_credentials():
    creds_json = os.getenv("GCP_SERVICE_ACCOUNT")

    if not creds_json:
        raise ValueError("Missing GCP_SERVICE_ACCOUNT secret")

    creds_dict = json.loads(creds_json)

    return Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )




def get_sheets_service():
    creds = get_credentials()
    return build('sheets', 'v4', credentials=creds)




def clean_value(x):
    if pd.isna(x):
        return ""

    if isinstance(x, pd.Timestamp):
        return x.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(x, np.generic):
        return x.item()

    return x


def prepare_sheet_rows(commodities):
    df = pd.DataFrame(commodities)

    today = date.today().isoformat()

    rows = []

    for _, r in df.iterrows():
        rows.append([
            today,
            clean_value(r.get("commodity")),
            clean_value(r.get("price_usd")),
            clean_value(r.get("price_inr")),
            clean_value(r.get("unit")),
            clean_value(r.get("last_updated")),
            clean_value(r.get("source"))
        ])

    return rows

def get_existing_dates(service, spreadsheet_id, sheet_name="Sheet1"):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A:A"
    ).execute()

    values = result.get("values", [])

    return set(row[0] for row in values[1:] if row)


def append_to_sheets(service, data_rows, spreadsheet_id, sheet_name):
    body = {"values": data_rows}

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=sheet_name,
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()


def update_google_sheets_pipeline(rows, RAW_SPREADSHEET_ID, TRAINING_SPREADSHEET_ID):

    service = get_sheets_service()
    today = date.today().isoformat()

    existing_dates = get_existing_dates(service, RAW_SPREADSHEET_ID)

    if today in existing_dates:
        print("Today's data already exists")
        return "exists"

    # ----------------------------
    # 1. Append RAW data
    # ----------------------------
    append_to_sheets(service, rows, RAW_SPREADSHEET_ID, "Sheet1")
    print("Raw data appended")

    # ----------------------------
    # 2. Training sheets mapping
    # ----------------------------
    commodity_map = {
        "Zinc Metal": "zinc",
        "Natural Rubber (India - RSS4)": "rubber",
        "Crude Palm Oil": "cpo",
        "Crude Oil (Indian Basket)": "crudeoil",
        "Brent Crude": "brentcrude",
        "Zinc Dross": "zincdross",
        "Zinc Oxide": "zincoxide"
    }

    # ----------------------------
    # 3. Append per commodity
    # ----------------------------
    for row in rows:
        date_value = row[0]
        commodity = row[1]
        price_usd = row[2]

        sheet_name = commodity_map.get(commodity)

        if not sheet_name:
            print(f"Skipping unmapped commodity: {commodity}")
            continue

        append_to_sheets(
            service,
            [[date_value, price_usd]],
            TRAINING_SPREADSHEET_ID,
            sheet_name
        )

    print("Training sheets updated")
    return "updated"

import pandas as pd


def load_sheet(service, spreadsheet_id, sheet_name):
    """
    Load sheet into DataFrame
    Expected columns: date, price_usd (or price)
    """

    try:
        # ----------------------------
        # 1. Fetch data
        # ----------------------------
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A:B"
        ).execute()

        values = result.get("values", [])

        if not values or len(values) < 2:
            return pd.DataFrame(columns=["date", "price"])

        # ----------------------------
        # 2. Build DataFrame
        # ----------------------------
        df = pd.DataFrame(values[1:], columns=values[0])
        df.columns = df.columns.str.strip().str.lower()

        # ----------------------------
        # 3. Standardize column names
        # ----------------------------
        if "price_usd" in df.columns:
            df = df.rename(columns={"price_usd": "price"})

        if "price" not in df.columns or "date" not in df.columns:
            raise ValueError(f"Sheet {sheet_name} missing required columns")

        # ----------------------------
        # 4. Clean data
        # ----------------------------
        df["price"] = (
            df["price"]
            .astype(str)
            .str.replace(",", "")
        )

        df["price"] = pd.to_numeric(df["price"], errors="coerce")

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce",
            dayfirst=True
        )

        # ----------------------------
        # 5. Drop invalid rows
        # ----------------------------
        df = df.dropna(subset=["date", "price"])

        # ----------------------------
        # 6. Sort
        # ----------------------------
        df = df.sort_values("date")

        return df

    except Exception as e:
        print(f"[load_sheet ERROR] {sheet_name}: {e}")
        return pd.DataFrame(columns=["date", "price"])