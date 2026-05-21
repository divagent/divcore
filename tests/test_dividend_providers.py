from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from app.providers.alpha_vantage_dividend_provider import AlphaVantageDividendProvider
from app.providers.nasdaq_dividend_provider import normalize_nasdaq_df


def test_nasdaq_provider_normalizes_rows():
    rows = normalize_nasdaq_df(
        pd.DataFrame(
            [
                {
                    "companyName": "Microsoft",
                    "symbol": "msft",
                    "dividend_Ex_Date": "06/01/2026",
                    "payment_Date": "06/15/2026",
                    "record_Date": "06/02/2026",
                    "dividend_Rate": "$1.25",
                    "indicated_Annual_Dividend": "5.00",
                    "announcement_Date": "05/01/2026",
                }
            ]
        )
    )

    assert len(rows) == 1
    assert rows[0].symbol == "MSFT"
    assert rows[0].dividend_ex_date == date(2026, 6, 1)
    assert rows[0].dividend_rate == Decimal("1.25")
    assert rows[0].source == "nasdaq"
    assert rows[0].confirmed is True


class _Response:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    def raise_for_status(self):
        return None

    async def json(self):
        return {
            "data": [
                {
                    "ex_dividend_date": "2026-06-01",
                    "declaration_date": "2026-05-01",
                    "record_date": "2026-06-02",
                    "payment_date": "2026-06-15",
                    "amount": "1.25",
                },
                {
                    "ex_dividend_date": "2027-06-01",
                    "amount": "9.99",
                },
            ]
        }


class _Session:
    def get(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return _Response()


@pytest.mark.asyncio
async def test_alpha_vantage_provider_filters_and_normalizes_rows():
    session = _Session()
    provider = AlphaVantageDividendProvider(api_key="test-key", session=session)

    rows = await provider.fetch_symbol_dividends(
        "msft",
        date(2026, 1, 1),
        date(2026, 12, 31),
    )

    assert len(rows) == 1
    assert rows[0].symbol == "MSFT"
    assert rows[0].dividend_ex_date == date(2026, 6, 1)
    assert rows[0].dividend_rate == Decimal("1.25")
    assert rows[0].source == "alpha_vantage"
    assert rows[0].confirmed is False
    assert session.kwargs["params"]["function"] == "DIVIDENDS"
