from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class NormalizedDividendRow:
    company_name: str | None
    symbol: str
    dividend_ex_date: date | None
    record_date: date | None
    payment_date: date | None
    dividend_rate: Decimal | None
    indicated_annual_dividend: Decimal | None
    announcement_date: date | None
    source: str
    source_updated_at: date | None = None
    confirmed: bool = False

    def to_div_record(self) -> dict:
        return {
            "company_name": self.company_name,
            "symbol": self.symbol,
            "dividend_ex_date": self.dividend_ex_date,
            "record_date": self.record_date,
            "payment_date": self.payment_date,
            "dividend_rate": self.dividend_rate,
            "indicated_annual_dividend": self.indicated_annual_dividend,
            "announcement_date": self.announcement_date,
        }


class DividendProvider(Protocol):
    async def fetch_dividends(
        self,
        date_from: date,
        date_to: date,
    ) -> list[NormalizedDividendRow]:
        ...
