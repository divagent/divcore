# app/service/ser_dividend_load.py
import csv, pandas as pd
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete

from app.db.models.m_div import Div  # your ORM model
# from app.service.service_div_inject import map_df_to_div_records  # helper to convert df to dict records for upsert

DATE_FMT = "%m/%d/%Y"  # Nasdaq CSV date format


class DividendCsvLoader:

    @staticmethod
    async def load_csv(db: AsyncSession, filename: str) -> int:
        """
        Read a CSV (normalized) and insert into DB.

        Returns:
            Number of rows inserted
        """
        inserted = 0
        file_path = f"data/dividends/{filename}"

        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                dividend = Div(
                    company_name=row["companyName"],
                    symbol=row["symbol"],
                    dividend_ex_date=datetime.strptime(row["dividend_Ex_Date"], DATE_FMT).date(),
                    payment_date=datetime.strptime(row["payment_Date"], DATE_FMT).date(),
                    record_date=datetime.strptime(row["record_Date"], DATE_FMT).date(),
                    dividend_rate=float(row["dividend_Rate"]),
                    indicated_annual_dividend=float(row["indicated_Annual_Dividend"]),
                    announcement_date=datetime.strptime(row["announcement_Date"], DATE_FMT).date(),
                )

                db.add(dividend)
                inserted += 1

        await db.commit()
        return inserted


class DivDfLoader:

    @staticmethod
    async def load_df(db: AsyncSession, df: pd.DataFrame) -> int:
        inserted = 0

        for _, row in df.iterrows():
            dividend = Div(
                company_name=row["companyName"],
                symbol=row["symbol"],
                dividend_ex_date=datetime.strptime(row["dividend_Ex_Date"], DATE_FMT).date(),
                payment_date=datetime.strptime(row["payment_Date"], DATE_FMT).date(),
                record_date=datetime.strptime(row["record_Date"], DATE_FMT).date(),
                dividend_rate=float(row["dividend_Rate"]),
                indicated_annual_dividend=float(row["indicated_Annual_Dividend"]),
                announcement_date=datetime.strptime(row["announcement_Date"], DATE_FMT).date(),
            )

            db.add(dividend)
            inserted += 1

        await db.commit()
        return inserted


    @staticmethod
    async def upsert_df_symbol_only(
        db: AsyncSession,
        df: pd.DataFrame,
    ) -> int:
        """
        Bulk upsert dividends by symbol only.
        Returns number of rows attempted.
        """
        if df is None or df.empty:
            return 0

        rows = [
            {
                "company_name": r["companyName"],
                "symbol": r["symbol"],
                "dividend_ex_date": datetime.strptime(r["dividend_Ex_Date"], DATE_FMT).date(),
                "record_date": datetime.strptime(r["record_Date"], DATE_FMT).date(),
                "payment_date": datetime.strptime(r["payment_Date"], DATE_FMT).date(),
                "dividend_rate": float(r["dividend_Rate"]),
                "indicated_annual_dividend": float(r["indicated_Annual_Dividend"]),
                "announcement_date": datetime.strptime(r["announcement_Date"], DATE_FMT).date(),
            }
            for r in df.to_dict(orient="records")
        ]

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
        await db.commit()
        return len(rows)
    
    
    # @staticmethod
    # async def upsert_dividends(db: AsyncSession, df: pd.DataFrame):
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
    async def delete_past(db: AsyncSession, today: date) -> int:
        stmt = delete(Div).where(Div.dividend_ex_date < today)
        result = await db.execute(stmt)
        await db.commit()
        return result.closed
