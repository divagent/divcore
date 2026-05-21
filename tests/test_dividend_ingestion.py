from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from app.providers.dividend_provider import NormalizedDividendRow
from app.service.ser_div_pg_load2pg import DivDfLoader
from app.service.service_div_inject import DivServicePg


class _Scalars:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return _Scalars(self._rows)


class _FakeDb:
    def __init__(self, symbols=None):
        self.symbols = symbols or []
        self.insert_stmt = None
        self.commits = 0

    async def execute(self, stmt):
        if stmt.__class__.__name__ == "Insert":
            self.insert_stmt = stmt
            return _Result([])
        return _Result(self.symbols)

    async def commit(self):
        self.commits += 1


def _nasdaq_df(rows):
    return pd.DataFrame(rows)


def _insert_values(stmt):
    values = stmt._multi_values[0]
    return [
        {column.key: value for column, value in row.items()}
        for row in values
    ]


@pytest.mark.asyncio
async def test_upsert_df_symbol_only_keeps_latest_duplicate_symbol():
    db = _FakeDb()
    df = _nasdaq_df(
        [
            {
                "companyName": "Old Microsoft",
                "symbol": "MSFT",
                "dividend_Ex_Date": "01/01/2026",
                "payment_Date": "01/02/2026",
                "record_Date": "01/03/2026",
                "dividend_Rate": "1.00",
                "indicated_Annual_Dividend": "4.00",
                "announcement_Date": "12/01/2025",
            },
            {
                "companyName": "New Microsoft",
                "symbol": "MSFT",
                "dividend_Ex_Date": "02/01/2026",
                "payment_Date": "02/02/2026",
                "record_Date": "02/03/2026",
                "dividend_Rate": "2.00",
                "indicated_Annual_Dividend": "8.00",
                "announcement_Date": "01/01/2026",
            },
        ]
    )

    count = await DivDfLoader.upsert_df_symbol_only(db, df)

    values = _insert_values(db.insert_stmt)
    assert count == 1
    assert len(values) == 1
    assert values[0]["symbol"] == "MSFT"
    assert values[0]["company_name"] == "New Microsoft"
    assert values[0]["dividend_ex_date"] == date(2026, 2, 1)
    assert db.commits == 0


class _Provider:
    async def fetch_dividends(self, date_from, date_to):
        return [
            NormalizedDividendRow(
                company_name="Microsoft",
                symbol="MSFT",
                dividend_ex_date=date(2026, 6, 1),
                record_date=date(2026, 6, 2),
                payment_date=date(2026, 6, 3),
                dividend_rate=Decimal("1.00"),
                indicated_annual_dividend=Decimal("4.00"),
                announcement_date=date(2026, 5, 1),
                source="nasdaq",
                confirmed=True,
            ),
            NormalizedDividendRow(
                company_name="Unknown Inc",
                symbol="NOPE",
                dividend_ex_date=date(2026, 6, 1),
                record_date=date(2026, 6, 2),
                payment_date=date(2026, 6, 3),
                dividend_rate=Decimal("1.00"),
                indicated_annual_dividend=Decimal("4.00"),
                announcement_date=date(2026, 5, 1),
                source="nasdaq",
                confirmed=True,
            ),
        ]


@pytest.mark.asyncio
async def test_nasdaq_ingestion_skips_symbols_outside_universe():
    db = _FakeDb(symbols=["MSFT"])

    result = await DivServicePg.from_nasdaq_2pg_4wk(
        db,
        date(2026, 5, 21),
        provider=_Provider(),
    )

    values = _insert_values(db.insert_stmt)
    assert result["inserted_or_updated"] == 1
    assert result["skipped_not_in_universe"] == 1
    assert result["source"] == "nasdaq"
    assert result["date_range"] == {
        "from": "2026-05-21",
        "to": "2026-07-02",
    }
    assert [row["symbol"] for row in values] == ["MSFT"]
