# app/service/ser_dividend_grab.py
import httpx
import requests, csv
import pandas as pd
from pathlib import Path

from app.config import get_settings_singleton
from app.providers.finnhub_client import FinnhubClient
settings=get_settings_singleton()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}

# Expected columns for validation
EXPECTED_COLUMNS = {
    "companyName",
    "symbol",
    "dividend_Ex_Date",
    "payment_Date",
    "record_Date",
    "dividend_Rate",
    "indicated_Annual_Dividend",
    "announcement_Date",
}

# from webpage
def grab_nasdaq_to_df(target_date: str) -> pd.DataFrame:
    r = requests.get(
        settings.NASDAQ_URL,
        params={"date": target_date},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()

    rows = r.json()["data"]["calendar"]["rows"]
    df = pd.DataFrame(rows)

    # Validate CSV columns
    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing columns from Nasdaq payload: {missing}")
    return df


# from google sheet
def grab_googlesheet_to_df() -> pd.DataFrame:
    df_google = pd.read_csv(settings.GOOGLE_SHEET_URL).dropna(how='all').reset_index(drop=True)
    return df_google


# from api
async def grab_symbol_list_form_finnhub() -> list[dict]:
    """Fetch US stock symbols from Finnhub"""
    client = FinnhubClient()
    us_symbol = client.get_us_symbols()
    return us_symbol


async def grab_symbol_list_form_finnhub_to_csv() -> list[dict]:
    """Fetch US stock symbols from Finnhub"""
    LOCAL_CSV_PATH = Path("data") / "finnhub_us_symbols.csv"
    client = FinnhubClient()
    us_symbol = client.get_us_symbols()
    if us_symbol:
        # Save to CSV
        with LOCAL_CSV_PATH.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=us_symbol[0].keys())
            writer.writeheader()
            writer.writerows(us_symbol)
    return us_symbol
