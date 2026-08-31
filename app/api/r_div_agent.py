from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncConnection

from app.agent.ag1.agent_loop import run_agent_loop
from app.agent.age_executor import run_agent_executor
from app.service.ser_ai_rag import rag_query
from app.agent.ag1.ag_core import run_agent
from app.db.conn.db_async import get_db
from app.schemas.sch_predict import PredictRequest, PredictResponse
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


@agentRou.post("/predict_dividend", response_model=PredictResponse)
async def predict_dividend_endpoint(
    req: PredictRequest,
    db: AsyncConnection = Depends(get_db),
):
    """Analyze a dividend from the frontend's authoritative facts and return all
    three labeled layers (facts / pattern / research), optionally publishing one
    idempotent all-day event per ex-date to the public Google Calendar.

    The facts in the body are authoritative — the backend echoes them verbatim and
    never re-fetches them. See src/data/ai-query.contract.md in the frontend repo.
    """
    return await predict_and_publish(
        req, db, trace_id=f"api:{req.symbol.strip().upper()}"
    )