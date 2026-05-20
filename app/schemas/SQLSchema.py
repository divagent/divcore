from pydantic import BaseModel
from typing import Optional


class SQLSearchSchema(BaseModel):
    account_id: Optional[str] = None
    company: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    lead_owner: Optional[str] = None
    deal_stage: Optional[str] = None
    source: Optional[str] = None
    limit: int = 50
