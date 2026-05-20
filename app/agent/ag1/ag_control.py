# app/agent/control.py
from typing import Literal
from pydantic import BaseModel

class AgentAction(BaseModel):
    action: Literal[
        "SKIP_RAG",
        "SINGLE_SEARCH",
        "MULTI_SEARCH",
        "REFUSE"
    ]

    reason: str
