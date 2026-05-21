
from app.db.models.m_div import Div


def div_to_content(div: Div) -> str:
    def field(name: str):
        if isinstance(div, dict):
            return div.get(name)
        return getattr(div, name)

    return f"""
        Company Name: {field("company_name")}
        Symbol: {field("symbol")}

        Dividend Ex-Date: {field("dividend_ex_date")}
        Record Date: {field("record_date")}
        Payment Date: {field("payment_date")}
        Announcement Date: {field("announcement_date")}

        Dividend Rate: {field("dividend_rate")}
        Indicated Annual Dividend: {field("indicated_annual_dividend")}
        Yield (%): {field("yield_percent")}

        Latest Price: {field("latest_price")}
        Market Cap: {field("market_cap")}
        """.strip()
