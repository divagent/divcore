# app/agent/schema.py
from pydantic import BaseModel, Field
from typing import List, Literal
from typing import Optional, Literal

class AgentDecision(BaseModel):
    thought: str = Field(description="The reasoning behind the next step")
    tool: Optional[Literal["get_dividend_data"]] = Field(None, description="The tool to call")
    tool_input: Optional[str] = Field(None, description="The search query for the tool")
    answer: Optional[str] = Field(None, description="The final answer to the user")
    
    

class AgentDecisionSchema(BaseModel):
    use_search: bool = Field(
        description="Whether dividend knowledge base search is required"
    )

    time_horizon: Literal[
        "historical",
        "next_week",
        "next_month",
        "unknown"
    ]

    symbols: List[str] = Field(
        description="Stock symbols explicitly mentioned or inferred"
    )

    intent: Literal[
        "knowledge",
        "screening",
        "decision",
        "risk_check"
    ]

    reasoning: str = Field(
        description="Short justification for the decision"
    )



# app/schemas/agent_result.py
from typing import List, Literal, Optional
from pydantic import BaseModel

class AgentResult(BaseModel):
    status: Literal[
        "ANSWER",
        "LOW_CONFIDENCE",
        "NO_DATA",
        "REFUSED"
    ]

    answer: Optional[str] = None
    confidence: Optional[float] = None
    sources: List[str] = []
    reason: Optional[str] = None
