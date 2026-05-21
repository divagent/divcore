# app/service/ser_dividend_load.py
import csv, pandas as pd
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete, select

from app.db.models.m_div import Div  # your ORM model
from app.db.models.m_symbols import Symbols
from app.providers.dividend_provider import NormalizedDividendRow
from app.providers.nasdaq_dividend_provider import normalize_nasdaq_df
# from app.service.service_div_inject import map_df_to_div_records  # helper to convert df to dict records for upsert

DATE_FMT = "%m/%d/%Y"  # Nasdaq CSV date format


class DividendCsvLoader:

    @staticmethod
    async def load_csv(db: AsyncConnection, filename: str) -> int:
        """
        Read a CSV (normalized) and insert into DB.

        Returns:
            Number of rows inserted
        """
        file_path = f"data/dividends/{filename}"
        rows: list[dict] = []

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                rows.append(
                    {
                        "company_name": row["companyName"],
                        "symbol": row["symbol"],
                        "dividend_ex_date": datetime.strptime(row["dividend_Ex_Date"], DATE_FMT).date(),
                        "payment_date": datetime.strptime(row["payment_Date"], DATE_FMT).date(),
                        "record_date": datetime.strptime(row["record_Date"], DATE_FMT).date(),
                        "dividend_rate": float(row["dividend_Rate"]),
                        "indicated_annual_dividend": float(row["indicated_Annual_Dividend"]),
                        "announcement_date": datetime.strptime(row["announcement_Date"], DATE_FMT).date(),
                    }
                )

                # ORM/session style was:
                # dividend = Div(...)
                # db.add(dividend)

        if rows:
            await db.execute(insert(Div), rows)
        # With AsyncConnection from async_engine.begin(), commit happens at context exit.
        # ORM/session style was: await db.commit()
        return len(rows)


class DivDfLoader:
    @staticmethod
    def _dedupe_latest_by_symbol(rows: list[dict]) -> list[dict]:
        latest_by_symbol: dict[str, dict] = {}
        for row in rows:
            symbol = str(row.get("symbol") or "").strip().upper()
            if not symbol:
                continue
            row["symbol"] = symbol
            latest_by_symbol[symbol] = row
        return list(latest_by_symbol.values())

    @staticmethod
    async def get_symbol_universe(db: AsyncConnection) -> set[str]:
        result = await db.execute(select(Symbols.symbol))
        return {
            str(symbol).strip().upper()
            for symbol in result.scalars().all()
            if symbol
        }

    @staticmethod
    def filter_records_to_universe(
        rows: list[NormalizedDividendRow],
        valid_symbols: set[str],
    ) -> tuple[list[NormalizedDividendRow], int]:
        filtered: list[NormalizedDividendRow] = []
        skipped = 0

        for row in rows:
            if row.symbol.upper() in valid_symbols:
                filtered.append(row)
            else:
                skipped += 1

        return filtered, skipped

    @staticmethod
    async def load_df(db: AsyncConnection, df: pd.DataFrame) -> int:
        rows: list[dict] = []

        for _, row in df.iterrows():
            rows.append(
                {
                    "company_name": row["companyName"],
                    "symbol": row["symbol"],
                    "dividend_ex_date": datetime.strptime(row["dividend_Ex_Date"], DATE_FMT).date(),
                    "payment_date": datetime.strptime(row["payment_Date"], DATE_FMT).date(),
                    "record_date": datetime.strptime(row["record_Date"], DATE_FMT).date(),
                    "dividend_rate": float(row["dividend_Rate"]),
                    "indicated_annual_dividend": float(row["indicated_Annual_Dividend"]),
                    "announcement_date": datetime.strptime(row["announcement_Date"], DATE_FMT).date(),
                }
            )

            # ORM/session style was:
            # dividend = Div(...)
            # db.add(dividend)

        if rows:
            await db.execute(insert(Div), rows)
        # ORM/session style was: await db.commit()
        return len(rows)


    @staticmethod
    async def upsert_df_symbol_only(
        db: AsyncConnection,
        df: pd.DataFrame,
    ) -> int:
        """
        Bulk upsert dividends by symbol only.
        Returns number of rows attempted.
        """
        if df is None or df.empty:
            return 0

        return await DivDfLoader.upsert_normalized_rows(
            db,
            normalize_nasdaq_df(df),
        )

    @staticmethod
    async def upsert_normalized_rows(
        db: AsyncConnection,
        dividend_rows: list[NormalizedDividendRow],
    ) -> int:
        rows = DivDfLoader._dedupe_latest_by_symbol(
            [
                row.to_div_record()
                for row in dividend_rows
                if row.symbol
            ]
        )

        if not rows:
            return 0

        stmt = insert(Div).values(rows)

        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol"],  # symbol-only uniqueness
            set_={
                "company_name": stmt.excluded.company_name,
                "dividend_ex_date": stmt.excluded.dividend_ex_date,
                "record_date": stmt.excluded.record_date,
                "payment_date": stmt.excluded.payment_date,
                "dividend_rate": stmt.excluded.dividend_rate,
                "indicated_annual_dividend": stmt.excluded.indicated_annual_dividend,
                "announcement_date": stmt.excluded.announcement_date,
            },
        )

        await db.execute(stmt)
        # ORM/session style was: await db.commit()
        return len(rows)
    
    
    # @staticmethod
    # async def upsert_dividends(db, df: pd.DataFrame):
    #     records = map_df_to_div_records(df)
    #     total = 0

    #     for record in records:
    #         stmt = insert(Div).values(**record)
    #         # ON CONFLICT on unique index: symbol + dividend_ex_date
    #         stmt = stmt.on_conflict_do_update(
    #             index_elements=['symbol', 'dividend_ex_date'],
    #             set_={
    #                 "company_name": record["company_name"],
    #                 "dividend_rate": record["dividend_rate"],
    #                 "payment_date": record["payment_date"],
    #                 "yield_percent": record["yield_percent"],
    #                 # update other columns as needed
    #             }
    #         )
    #         await db.execute(stmt)
    #         total += 1

    #     await db.commit()
    #     return total

    


class DivClean:
    
    @staticmethod
    async def delete_past(db: AsyncConnection, today: date) -> int:
        stmt = delete(Div).where(Div.dividend_ex_date < today)
        result = await db.execute(stmt)
        # ORM/session style was: await db.commit()
        return result.rowcount or 0
