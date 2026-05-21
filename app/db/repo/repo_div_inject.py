# app/repositories/dividend_repo.py
import csv
from decimal import Decimal
from pathlib import Path
from typing import Any, List
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy import select, update
from sqlalchemy.engine import Result
from sqlalchemy.dialects.postgresql import insert

from app.db.models.m_div import Div
from app.db.models.m_symbols import Symbols


class DividendRepo:
    def __init__(self, db: AsyncConnection):
        self.db = db

    # -------------------------
    # Query Methods
    # -------------------------
    async def get_by_symbol(self, symbol: str) -> List[dict[str, Any]]:
        """Return all Div rows for a given symbol."""
        result = await self.db.execute(
            select(Div.__table__).where(Div.symbol == symbol)
        )
        # ORM/session style was:
        # result = await self.db.execute(select(Div).where(Div.symbol == symbol))
        # return list(result.scalars().all())
        return [dict(row) for row in result.mappings().all()]

    async def get_all(self) -> List[dict[str, Any]]:
        """Return all Div rows."""
        result = await self.db.execute(select(Div.__table__))
        # ORM/session style was:
        # result = await self.db.execute(select(Div))
        # return list(result.scalars().all())
        return [dict(row) for row in result.mappings().all()]

    # -------------------------
    # Update / Modify Methods
    # -------------------------
    async def update_market_data(
        self,
        rows: List[dict[str, Any]],
        latest_price: Decimal,
        market_cap: Decimal,
        commit: bool = False,
    ) -> int:
        """
        Update latest_price, market_cap, and recompute yield_percent.
        If commit=True, commits automatically.
        Returns the number of rows updated.
        """
        updated = 0
        for row in rows:
            indicated_annual_dividend = row.get("indicated_annual_dividend")
            yield_percent = None
            if indicated_annual_dividend and latest_price > 0:
                yield_percent = Decimal(indicated_annual_dividend) / latest_price * Decimal("100")

            await self.db.execute(
                update(Div)
                .where(Div.id == row["id"])
                .values(
                    latest_price=latest_price,
                    market_cap=market_cap,
                    yield_percent=yield_percent,
                )
            )

            # ORM/session style was:
            # row.latest_price = latest_price
            # row.market_cap = market_cap
            # row.yield_percent = yield_percent
            updated += 1

        if commit:
            # Commit is managed by AsyncConnection lifecycle.
            # ORM/session style was: await self.db.commit()
            pass

        return updated

    # -------------------------
    # Bulk Upsert Example
    # -------------------------
    async def google_bulk_upsert(self, records: list[dict], conflict_keys: list[str]) -> int:
        if not records:
            return 0

        stmt = insert(Div).values(records)
        # Update only columns in records, skip conflict keys
        update_cols = {k: stmt.excluded[k] for k in records[0].keys() if k not in conflict_keys}
        stmt = stmt.on_conflict_do_update(index_elements=conflict_keys, set_=update_cols)

        result: Result = await self.db.execute(stmt)
        # ORM/session style was: await self.db.commit()

        # Runtime-safe rowcount
        return getattr(result, "rowcount", 0)


    async def finnhub_symbol_upsert_loop_csv(self) -> int:
        inserted_or_updated = 0
        csv_path = Path("data") / "finnhub_us_symbols.csv"

        with csv_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                symbol_val = row.get("symbol")
                if not symbol_val:
                    continue  # skip empty symbol

                values = {
                    "symbol": symbol_val,
                    "symbol2": row.get("symbol2"),
                    "type": row.get("type"),
                    "displaySymbol": row.get("displaySymbol"),
                    "currency": row.get("currency"),
                    "figi": row.get("figi"),
                    "isin": row.get("isin"),
                    "mic": row.get("mic"),
                    "shareClassFIGI": row.get("shareClassFIGI"),
                    "description": row.get("description"),
                }
                stmt = insert(Symbols).values(values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["symbol"],
                    set_={k: stmt.excluded[k] for k in values if k != "symbol"},
                )
                await self.db.execute(stmt)

                # ORM/session style was:
                # existing = result.scalars().first()
                # if existing:
                #     existing.symbol2 = row.get("symbol2")
                #     ...
                # else:
                #     new_obj = Symbols(...)
                #     self.db.add(new_obj)

                inserted_or_updated += 1
                print(inserted_or_updated, symbol_val)

                # ORM/session style batched commits were:
                # if inserted_or_updated % 500 == 0:
                #     await self.db.commit()

        # ORM/session style was: await self.db.commit()
        return inserted_or_updated
    

    async def sync_div_type_from_symbols(self) -> int:
        stmt = (
            update(Div)
            .where(Div.symbol == Symbols.symbol)
            .values(company_type=Symbols.type)
        )

        result = await self.db.execute(stmt)
        # ORM/session style was: await self.db.commit()

        return result.rowcount # type: ignore[attr-defined]
