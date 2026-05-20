from pydantic import BaseModel
from typing import List, Optional

class QueryString(BaseModel):
    query: str = "How to lose weight fast?"
    top_k: int = 50
class QueryList(BaseModel):
    queries: List[str]



class ResultString(BaseModel):
    result: str

class ResultList(BaseModel):
    results: list[dict]  # list of dicts from SQL query
    
    