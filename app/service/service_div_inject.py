# app/service/ser_dividend_load.py
import csv
import pandas as pd
from datetime import datetime, date
from datetime import date, timedelta
from dateutil import parser
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete, func, or_

from app.db.models.m_div import Div  # your ORM model
from app.db.repo.repo_div_inject import DividendRepo
from app.providers.dividend_provider import DividendProvider
from app.providers.nasdaq_dividend_provider import NasdaqDividendProvider
from app.service.ser_div_pg_load2pg import DivDfLoader
from app.util.util_grab_div import grab_googlesheet_to_df, grab_symbol_list_form_finnhub

DATE_FMT = "%m/%d/%Y"  # Nasdaq CSV date format


def parse_flexible_date(date_str):
    try:
        return parser.parse(date_str, fuzzy=True).date()
    except:
        return None


class DivServicePg:

    @staticmethod
    async def delete_past(db: AsyncConnection, today: date) -> int:
        stmt = delete(Div).where(Div.dividend_ex_date <= today)
        result = await db.execute(stmt)
        # ORM/session style was: await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def delete_preferred(db: AsyncConnection) -> int:
        stmt = delete(Div).where(
            or_(
                Div.company_name.ilike("%Preferred Unit%"),
                Div.company_name.ilike("%Preferred S%"),
                Div.company_name.ilike("%ETN%"),
            )
        )
        result = await db.execute(stmt)
        # ORM/session style was: await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def prune_marketcap_anomalies(db: AsyncConnection) -> int:
        MIN_MARKETCAP = 1_000        # 1B
        MAX_MARKETCAP = 5_000_000    # 5T

        stmt = delete(Div).where(
            (Div.market_cap < MIN_MARKETCAP) |
            (Div.market_cap > MAX_MARKETCAP) |
            (Div.market_cap.is_(None))
        )

        result = await db.execute(stmt)
        # ORM/session style was: await db.commit()
        return result.rowcount or 0

    @staticmethod
    async def prune_non_stock_type(db: AsyncConnection) -> int:
        EXCLUDED_DIV_TYPES = {"Closed-End Fund", "REIT", "PUBLIC"}
        stmt = delete(Div).where(
            (Div.div_type.is_(None)) |
            (func.trim(Div.div_type) == "") |
            (Div.div_type.in_(EXCLUDED_DIV_TYPES))
        )

        result = await db.execute(stmt)
        # ORM/session style was: await db.commit()

        return result.rowcount or 0

    @staticmethod
    async def from_nasdaq_2pg_4wk(
        db: AsyncConnection,
        today: date,
        provider: DividendProvider | None = None,
    ) -> dict:
        start = today
        weeks = 6
        end = start + timedelta(weeks=weeks)

        provider = provider or NasdaqDividendProvider()
        rows = await provider.fetch_dividends(start, end)
        symbol_universe = await DivDfLoader.get_symbol_universe(db)
        rows_to_import, skipped_not_in_universe = DivDfLoader.filter_records_to_universe(
            rows,
            symbol_universe,
        )
        inserted_or_updated = await DivDfLoader.upsert_normalized_rows(db, rows_to_import)

        return {
            "inserted_or_updated": inserted_or_updated,
            "skipped_not_in_universe": skipped_not_in_universe,
            "source": "nasdaq",
            "date_range": {
                "from": start.isoformat(),
                "to": end.isoformat(),
            },
        }

    @staticmethod
    def _from_google_to_df(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # extract symbol from "Company (XXX)"
        df["symbol"] = df["Company"].apply(
            lambda x: x.split("(")[-1].replace(")", "").strip()
            if isinstance(x, str) and "(" in x and ")" in x
            else None
        )

        return pd.DataFrame({
            "company_name": df["Company"],
            "symbol": df["symbol"],
            "dividend_ex_date": pd.to_datetime(df["Ex-Dividend Date"], errors="coerce").dt.date,
            "payment_date": pd.to_datetime(df["Payment Date"], errors="coerce").dt.date,
            "dividend_rate": pd.to_numeric(df["Dividend"], errors="coerce"),
            "yield_percent": (
                df["Yield"]
                .astype(str)
                .str.rstrip("%")
                .pipe(pd.to_numeric, errors="coerce")
            ),
            # fields Google doesn't have
            "record_date": None,
            "indicated_annual_dividend": None,
            "announcement_date": None,
            "latest_price": None,
            "market_cap": None,
        })

    @staticmethod
    async def from_google_sheet_to_pg(db: AsyncConnection) -> int:
        df_raw = grab_googlesheet_to_df()

        if df_raw is None or df_raw.empty:
            return 0

        for date_col in ['Ex-Dividend Date']:
            if date_col in df_raw.columns:
                df_raw[date_col] = df_raw[date_col].apply(parse_flexible_date)

        # Convert raw Google sheet DF to normalized Div DF
        df = DivServicePg._from_google_to_df(df_raw)
        df["dividend_rate"] = pd.to_numeric(
            df["dividend_rate"], errors="coerce")
        df = df[df["dividend_rate"] > 0]
        df = df.drop_duplicates(subset=['symbol'], keep='last')

        # Convert DF to list of dicts for bulk_upsert
        records = df.to_dict(orient='records')
        div_columns = ["company_name", "symbol",
                       "dividend_ex_date", "dividend_rate", "yield_percent"]
        records_cleaned = [{k: row[k] for k in div_columns} for row in records]
        # Create repository instance
        repo = DividendRepo(db)

        # Call async bulk_upsert
        return await repo.google_bulk_upsert(records_cleaned, conflict_keys=['symbol'])

    @staticmethod
    async def update_symbol_list(db: AsyncConnection) -> int:
        symbol_list = await grab_symbol_list_form_finnhub()

        upserted = await DividendRepo(db).finnhub_symbol_bulk_upsert(symbol_list)
        return upserted
