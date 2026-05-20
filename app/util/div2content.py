
from app.db.models.m_div import Div


def div_to_content(div: Div) -> str:
    return f"""
        Company Name: {div.company_name}
        Symbol: {div.symbol}

        Dividend Ex-Date: {div.dividend_ex_date}
        Record Date: {div.record_date}
        Payment Date: {div.payment_date}
        Announcement Date: {div.announcement_date}

        Dividend Rate: {div.dividend_rate}
        Indicated Annual Dividend: {div.indicated_annual_dividend}
        Yield (%): {div.yield_percent}

        Latest Price: {div.latest_price}
        Market Cap: {div.market_cap}
        """.strip()
