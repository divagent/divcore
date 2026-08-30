from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from app.agent.ag1.agent_loop import run_agent_loop
from app.agent.age_executor import run_agent_executor
from app.service.ser_ai_rag import rag_query
from app.agent.ag1.ag_core import run_agent
from app.db.conn.db_async import get_db
from app.service.ser_div_predict_publish import predict_and_publish

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


@agentRou.post("/predict_dividend")
async def predict_dividend_endpoint(
    symbol: str,
    db: AsyncConnection = Depends(get_db),
):
    """Predict the next dividend for a symbol, persist it, and publish it to the
    public Google Calendar (idempotent). Returns the prediction + calendar status."""
    return await predict_and_publish(symbol, db, trace_id=f"api:{symbol.upper()}")