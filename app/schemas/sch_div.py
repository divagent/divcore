from datetime import date
from pydantic import BaseModel, Field

class DividendBase(BaseModel):
    company_name: str = Field(..., max_length=255)
    symbol: str = Field(..., max_length=50)
    dividend_ex_date: date
    record_date: date
    payment_date: date
    dividend_rate: float
    indicated_annual_dividend: float
    announcement_date: date


class DividendCreate(DividendBase):
    pass


class DividendRead(DividendBase):
    id: int

    model_config = {
        "from_attributes": True
    }
