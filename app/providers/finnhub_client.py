# app/providers/finnhub_client.py
import os
import requests

FINNHUB_BASE = "https://finnhub.io/api/v1"

class FinnhubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("FINNHUB_API_KEY")
        if not self.token:
            raise RuntimeError("FINNHUB_API_KEY not set")

    def get_quote_and_profile(self, symbol: str) -> dict:
        quote = requests.get(
            f"{FINNHUB_BASE}/quote",
            params={"symbol": symbol, "token": self.token},
            timeout=10,
        ).json()

        profile = requests.get(
            f"{FINNHUB_BASE}/stock/profile2",
            params={"symbol": symbol, "token": self.token},
            timeout=10,
        ).json()
        
        print("quote:--------", quote, profile)
        print("profile    :--------", profile)

        return {
            "symbol": symbol,
            "latest_price": quote.get("c"),
            "market_cap": profile.get("marketCapitalization"),
        }


    def get_us_symbols(self) -> list[dict]:
        """Fetch all US stock symbols (exchange=US)"""
        resp = requests.get(
            f"{FINNHUB_BASE}/stock/symbol",
            params={"exchange": "US", "token": self.token},
            timeout=100,
        )
        resp.raise_for_status()
        return resp.json()