from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

from app.div_mcp.tools import serialize_dividend


def test_serialize_dividend_snapshot_item():
    row = SimpleNamespace(
        id=uuid4(),
        company_name="Microsoft",
        symbol="MSFT",
        dividend_ex_date=date(2026, 6, 1),
        record_date=date(2026, 6, 2),
        payment_date=date(2026, 6, 15),
        dividend_rate=Decimal("1.25"),
        indicated_annual_dividend=Decimal("5.00"),
        announcement_date=date(2026, 5, 1),
        latest_price=Decimal("420.50"),
        yield_percent=Decimal("1.20"),
        market_cap=Decimal("3000000.00"),
        div_type="Cash",
        company_type="Common Stock",
    )

    item = serialize_dividend(row)

    assert item["symbol"] == "MSFT"
    assert item["dividend_ex_date"] == "2026-06-01"
    assert item["dividend_rate"] == 1.25
