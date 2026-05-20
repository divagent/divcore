# app/service/ser_dividend_grab.py
import requests
from datetime import date, timedelta
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.service.service_div_inject import DivDfLoader
from app.util.util_grab_div import grab_nasdaq_to_df


class DividendPipeline:

    @staticmethod
    async def nasdaq2pg(db: AsyncSession, target_date: str) -> int:
        """
        Grab dividends from Nasdaq for the target date and load into PostgreSQL.

        Returns:
            Number of rows inserted
        """
        # Step 1: Grab dividends 
        df = grab_nasdaq_to_df(target_date=target_date)

        # Step 2: Load DataFrame into PostgreSQL
        inserted_count = await DivDfLoader.load_df(db, df)

        return inserted_count
    


    @staticmethod
    async def nasdaq_4w2pg(db: AsyncSession) -> int:
        """
        Grab dividends from today -> next 4 weeks and upsert into PostgreSQL.

        Returns:
            Number of rows inserted/updated
        """
        total = 0
        start = date.today()
        end = start + timedelta(weeks=1)

        cur = start
        print("start:", start, "end:", end)
        while cur <= end:
            try:
                df = grab_nasdaq_to_df(target_date=cur.strftime("%Y-%m-%d"))
                print(cur, "df.shape:", None if df is None else df.shape)

                if df is None or df.empty:
                    cur += timedelta(days=1)
                    continue

                total += await DivDfLoader.upsert_df_symbol_only(db, df)

            except Exception as e:
                # Ignore weekends/holidays / empty responses
                pass

            cur += timedelta(days=1)

        return total
    
