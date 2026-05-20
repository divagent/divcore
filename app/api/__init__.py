from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.r_div_inject import injRou
from app.api.r_div_show import divRou
from app.api.r_div_rag import ragRou
from app.api.r_div_agent import agentRou
from app.api.r_lc import lcRou

rou = APIRouter()

rou.include_router(divRou, prefix="/div_show", tags=["show PG, pgvector, Datalake, Azure Congnitive Search"])
rou.include_router(injRou, prefix="/div_inject", tags=["From Nasdaq to Postgres to Datalake"])
rou.include_router(ragRou, prefix="/div_rag_contract", tags=["RAG Contract"])

rou.include_router(agentRou, prefix="/div_agent", tags=["Agent"])
rou.include_router(lcRou, prefix="/langchain", tags=["LangChain"])


@rou.get("/")
def rouGet():
    return RedirectResponse(url="https://ainvoaice.com")
