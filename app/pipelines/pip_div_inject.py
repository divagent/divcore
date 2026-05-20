from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.pg_conn import get_db_auto
from app.service.service_div_inject import DivServicePg
from app.service.ser_dividend_finnhub import refresh_all_finnhub_market_data, refresh_finnhub_market_data
from app.db.repo.repo_div_inject import DividendRepo
from app.util.util_grab_div import grab_symbol_list_form_finnhub_to_csv

class DivPipeline:


    @staticmethod
    async def run_hourly() -> dict:
        enriched = refresh_all_finnhub_market_data()

        return {
            # "deleted_past": deleted,
            # "upserted": upserted,
            "enriched": enriched,
            # "Anomaly": pruned,
        }






    @staticmethod
    async def run_daily(db: AsyncSession, today: date) -> dict:
        upserted = await DivServicePg.from_nasdaq_2pg_4wk(db, today)
        deleted  = await DivServicePg.delete_past(db, today)
        deleted  = await DivServicePg.delete_preferred(db)
        # enriched = refresh_all_finnhub_market_data()
        # enriched = refresh_all_finnhub_market_data()
        # pruned = await DivServicePg.prune_marketcap_anomalies(db)

        return {
            "deleted_past": deleted,
            "upserted": upserted,
            # "enriched": enriched,
            # "Anomaly": pruned,
        }


    @staticmethod
    async def run_monthly(db: AsyncSession) -> dict:
        repo = DividendRepo(db)
        upserted = await DivServicePg.from_google_sheet_to_pg(db)   #step 1. 
        print("upserted:", upserted)
        sync_type = await repo.sync_div_type_from_symbols()   #step 2.
        print("sync_type:", sync_type)
        pruned_non_stock = await DivServicePg.prune_non_stock_type(db)  
        # print("pruned_non_stock:", pruned_non_stock)
        # pruned = await DivServicePg.prune_marketcap_anomalies(db)

        return {
            "upserted": upserted,
            "sync_type": sync_type,
            "pruned_non_stock": pruned_non_stock,
        }



    @staticmethod
    async def run_yearly(db: AsyncSession) -> dict:
        save2csv = await grab_symbol_list_form_finnhub_to_csv()
        csv2pg = await DividendRepo(db).finnhub_symbol_upsert_loop_csv()
        
        return {
            "upserted": save2csv,
            "csv2pg": csv2pg,
        }

