from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str


class AgentResponse(BaseModel):
    thought: str | None
    tool: str | None
    tool_input: str | None
    answer: str | None