# app/services/dividend_service.py
import time
from decimal import Decimal
from sqlalchemy import select, update

from app.db.db_sync import get_db_sync_contextmanager
from app.db.models.m_div import Div
from app.providers.finnhub_client import FinnhubClient


# Configurable limits
FINNHUB_RATE_LIMIT_PER_MIN = 29  # free tier approx 60 calls/minute

def refresh_finnhub_market_data(symbol: str) -> dict:
    client = FinnhubClient()
    data = client.get_quote_and_profile(symbol)

    # if data["latest_price"] is None or data["market_cap"] is None:
    #     raise ValueError("Incomplete data from Finnhub")

    # latest_price = Decimal(str(data["latest_price"]))
    # market_cap = Decimal(str(data["market_cap"]))
    
    latest_price = Decimal(str(data["latest_price"])) if data["latest_price"] is not None else Decimal("555.55")
    market_cap = Decimal(str(data["market_cap"])) if data["market_cap"] is not None else Decimal("555.55")

    # Service handles DB session internally
    with get_db_sync_contextmanager() as db:
        result = db.execute(select(Div.__table__).where(Div.symbol == symbol))
        rows = [dict(row) for row in result.mappings().all()]
        # ORM/session style was:
        # rows = DividendRepo.get_by_symbol(db, symbol)
        if not rows:
            raise LookupError(f"No dividend rows for symbol {symbol}")

        updated = 0
        for row in rows:
            indicated_annual_dividend = row.get("indicated_annual_dividend")
            yield_percent = None
            if indicated_annual_dividend and latest_price > 0:
                yield_percent = Decimal(indicated_annual_dividend) / latest_price * Decimal("100")

            db.execute(
                update(Div)
                .where(Div.id == row["id"])
                .values(
                    latest_price=latest_price,
                    market_cap=market_cap,
                    yield_percent=yield_percent,
                )
            )
            updated += 1

        # ORM/session style was: db.commit()

    return {
        "symbol": symbol,
        "latest_price": latest_price,
        "market_cap": market_cap,
        "rows_updated": updated,
    }


def ___refresh_all_finnhub_market_data_old() -> dict:
    client = FinnhubClient()

    # Only fetch symbols (detached-safe)
    with get_db_sync_contextmanager() as db:
        result = db.execute(select(Div.symbol))
        symbols = [row[0] for row in result.all()]
        # ORM/session style was: symbols = [row.symbol for row in get_all(db)]

    api_calls = 0
    minute_start = time.time()
    results = []

    for symbol in symbols:
        # rate limit
        elapsed = time.time() - minute_start
        if api_calls >= FINNHUB_RATE_LIMIT_PER_MIN:
            print(f"Rate limit reached, sleeping for {60 - elapsed:.2f} seconds")
            if elapsed < 60:
                time.sleep(60 - elapsed)
            api_calls = 0
            minute_start = time.time()

        try:
            data = client.get_quote_and_profile(symbol)

            if data["latest_price"] is None or data["market_cap"] is None:
                raise ValueError("Incomplete data")

            latest_price = Decimal(str(data["latest_price"]))
            market_cap = Decimal(str(data["market_cap"]))

            # ✅ load + update in SAME session
            with get_db_sync_contextmanager() as db:
                result = db.execute(select(Div.__table__).where(Div.symbol == symbol))
                rows = [dict(row) for row in result.mappings().all()]
                updated = 0
                for row in rows:
                    indicated_annual_dividend = row.get("indicated_annual_dividend")
                    yield_percent = None
                    if indicated_annual_dividend and latest_price > 0:
                        yield_percent = Decimal(indicated_annual_dividend) / latest_price * Decimal("100")
                    db.execute(
                        update(Div)
                        .where(Div.id == row["id"])
                        .values(
                            latest_price=latest_price,
                            market_cap=market_cap,
                            yield_percent=yield_percent,
                        )
                    )
                    updated += 1
                # ORM/session style was:
                # rows = get_by_symbol(db, symbol)
                # updated = update_market_data(...)
                # db.commit()

            results.append({
                "symbol": symbol,
                "rows_updated": updated,
            })

        except Exception as e:
            results.append({
                "symbol": symbol,
                "error": str(e),
            })

        api_calls += 1

    return {
        "symbols_processed": len(symbols),
        "results": results,
    }












def refresh_all_finnhub_market_data() -> dict:
    client = FinnhubClient()

    with get_db_sync_contextmanager() as db:
        result = db.execute(select(Div.__table__))
        divs = [dict(row) for row in result.mappings().all()]
        # ORM/session style was: divs = db.query(Div).all()

        api_calls = 0
        window_start = time.time()

        updated = 0
        skipped = 0

        for div in divs:
            if api_calls >= FINNHUB_RATE_LIMIT_PER_MIN:
                print(f"Rate limit reached, sleeping ")
                elapsed = time.time() - window_start
                if elapsed < 60:
                    time.sleep(60 - elapsed)
                api_calls = 0
                window_start = time.time()

            try:
                data = client.get_quote_and_profile(div["symbol"])

                price = data.get("latest_price")
                market_cap = data.get("market_cap")

                if price is None or market_cap is None:
                    skipped += 1
                    continue

                db.execute(
                    update(Div)
                    .where(Div.id == div["id"])
                    .values(
                        latest_price=Decimal(str(price)),
                        market_cap=Decimal(str(market_cap)),
                    )
                )
                # ORM/session style was:
                # div.latest_price = Decimal(str(price))
                # div.market_cap = Decimal(str(market_cap))

                updated += 1

            except Exception:
                skipped += 1

            api_calls += 1

        # ORM/session style was: db.commit()

    return {
        "rows": len(divs),
        "updated": updated,
        "skipped": skipped,
    }
