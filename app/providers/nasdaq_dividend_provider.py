from __future__ import annotations

import asyncio
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

import pandas as pd

from app.providers.dividend_provider import NormalizedDividendRow
from app.util.util_grab_div import grab_nasdaq_to_df


DATE_FMT = "%m/%d/%Y"


def _to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace("$", "").replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _to_date(value) -> date | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def normalize_nasdaq_df(df: pd.DataFrame) -> list[NormalizedDividendRow]:
    rows: list[NormalizedDividendRow] = []
    if df is None or df.empty:
        return rows

    for raw in df.to_dict(orient="records"):
        symbol = str(raw.get("symbol") or "").strip().upper()
        if not symbol:
            continue

        rows.append(
            NormalizedDividendRow(
                company_name=raw.get("companyName"),
                symbol=symbol,
                dividend_ex_date=_to_date(raw.get("dividend_Ex_Date")),
                record_date=_to_date(raw.get("record_Date")),
                payment_date=_to_date(raw.get("payment_Date")),
                dividend_rate=_to_decimal(raw.get("dividend_Rate")),
                indicated_annual_dividend=_to_decimal(raw.get("indicated_Annual_Dividend")),
                announcement_date=_to_date(raw.get("announcement_Date")),
                source="nasdaq",
                confirmed=True,
            )
        )

    return rows


class NasdaqDividendProvider:
    async def fetch_dividends(
        self,
        date_from: date,
        date_to: date,
    ) -> list[NormalizedDividendRow]:
        rows: list[NormalizedDividendRow] = []
        cur = date_from

        while cur <= date_to:
            try:
                df = await asyncio.to_thread(
                    grab_nasdaq_to_df,
                    target_date=cur.strftime("%Y-%m-%d"),
                )
                rows.extend(normalize_nasdaq_df(df))
            except Exception:
                pass

            cur += timedelta(days=1)

        return rows
