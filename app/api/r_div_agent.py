from fastapi import APIRouter
from app.agent.ag1.agent_loop import run_agent_loop
from app.agent.age_executor import run_agent_executor
from app.service.ser_ai_rag import rag_query
from app.agent.ag1.ag_core import run_agent

agentRou = APIRouter()


@agentRou.post("/chat_with_ag1")
async def chat_with_ag1(question: str):
    # result = await run_agent_loop(question)
    result = await run_agent_executor(question)
    return result


@agentRou.post("/chat_with_agent")
async def chat_with_agent(question: str):
    # result = await run_agent_loop(question)
    result = await run_agent_executor(question,"traceid1")
    return result