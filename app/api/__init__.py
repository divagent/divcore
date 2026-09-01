from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.api.r_div_show import divRou
from app.api.r_div_agent import agentRou

rou = APIRouter()

rou.include_router(divRou, prefix="/div_show", tags=["show PG"])
rou.include_router(agentRou, prefix="/div_agent", tags=["Agent"])


@rou.get("/")
def rouGet():
    return RedirectResponse(url="http://localhost:5173")
