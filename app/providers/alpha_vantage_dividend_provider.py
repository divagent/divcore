from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

import aiohttp

from app.config import get_settings_singleton
from app.providers.dividend_provider import NormalizedDividendRow


ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"


def _to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _to_date(value) -> date | None:
    if not value or value == "None":
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


class AlphaVantageDividendProvider:
    def __init__(
        self,
        api_key: str | None = None,
        session: aiohttp.ClientSession | None = None,
    ):
        settings = get_settings_singleton()
        self.api_key = api_key or settings.ALPHAVANTAGE_API_KEY
        self._session = session

    async def fetch_symbol_dividends(
        self,
        symbol: str,
        date_from: date,
        date_to: date,
    ) -> list[NormalizedDividendRow]:
        session = self._session
        owns_session = session is None
        if session is None:
            session = aiohttp.ClientSession()

        try:
            async with session.get(
                ALPHA_VANTAGE_URL,
                params={
                    "function": "DIVIDENDS",
                    "symbol": symbol,
                    "apikey": self.api_key,
                },
                timeout=30,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
        finally:
            if owns_session:
                await session.close()

        rows = payload.get("data", [])
        normalized: list[NormalizedDividendRow] = []
        for row in rows:
            ex_date = _to_date(row.get("ex_dividend_date"))
            if ex_date is None or ex_date < date_from or ex_date > date_to:
                continue

            normalized.append(
                NormalizedDividendRow(
                    company_name=None,
                    symbol=symbol.upper(),
                    dividend_ex_date=ex_date,
                    record_date=_to_date(row.get("record_date")),
                    payment_date=_to_date(row.get("payment_date")),
                    dividend_rate=_to_decimal(row.get("amount")),
                    indicated_annual_dividend=None,
                    announcement_date=_to_date(row.get("declaration_date")),
                    source="alpha_vantage",
                    confirmed=False,
                )
            )

        return normalized

    async def fetch_dividends(
        self,
        date_from: date,
        date_to: date,
        symbols: list[str] | None = None,
    ) -> list[NormalizedDividendRow]:
        if not symbols:
            return []

        rows: list[NormalizedDividendRow] = []
        for symbol in symbols:
            rows.extend(await self.fetch_symbol_dividends(symbol, date_from, date_to))
        return rows
