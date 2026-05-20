# main.py
import os
from fastapi import APIRouter
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.ag1.ag_core import run_agent
from app.lc.lc_agent_service import lc_run_agent

lcRou = APIRouter()

# ---- LLM (Azure OpenAI via LangChain) ----
llm = ChatOpenAI(
    model="gpt-5-nano",  # Azure DEPLOYMENT NAME
    base_url="https://haystacked.cognitiveservices.azure.com/openai/v1/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

# ---- Request schema ----
class ChatRequest(BaseModel):
    message: str

# ---- Agent endpoint ----
@lcRou.post("/agent/chat")
async def chat_agent(req: ChatRequest):
    messages = [
        SystemMessage(content="You are a helpful AI agent."),
        HumanMessage(content=req.message),
    ]

    response = llm.invoke(messages)

    return {
        "reply": response.content
    }



class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    result: str


@lcRou.post("/agent", response_model=AgentResponse)
async def agent_endpoint(payload: AgentRequest):
    """
    Thin HTTP wrapper over LangChain agent.
    """
    output = lc_run_agent(payload.message)
    return {"result": output}



@lcRou.post("/agent_final", response_model=AgentResponse)
async def agent_endpoint(payload: AgentRequest):
    """
    Thin HTTP wrapper over LangChain agent.
    """
    output = lc_run_agent(payload.message)
    return {"result": output}