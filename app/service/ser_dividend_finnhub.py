# app/services/dividend_service.py
import time
from decimal import Decimal
from app.db.db_sync import get_db_sync_contextmanager
from app.db.models.m_div import Div
from app.providers.finnhub_client import FinnhubClient
from app.db.repo.repo_div_inject import DividendRepo


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
        rows = DividendRepo.get_by_symbol(db, symbol)
        if not rows:
            raise LookupError(f"No dividend rows for symbol {symbol}")
        updated = DividendRepo.update_market_data(db, rows, latest_price, market_cap)
        db.commit()

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
        symbols = [row.symbol for row in get_all(db)]

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
                rows = get_by_symbol(db, symbol)
                updated = update_market_data(
                    db,
                    rows,
                    latest_price,
                    market_cap,
                )
                db.commit()

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
        divs = db.query(Div).all()

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
                data = client.get_quote_and_profile(div.symbol)

                price = data.get("latest_price")
                market_cap = data.get("market_cap")

                if price is None or market_cap is None:
                    skipped += 1
                    continue

                div.latest_price = Decimal(str(price))
                div.market_cap = Decimal(str(market_cap))

                updated += 1

            except Exception:
                skipped += 1

            api_calls += 1

        db.commit()

    return {
        "rows": len(divs),
        "updated": updated,
        "skipped": skipped,
    }
