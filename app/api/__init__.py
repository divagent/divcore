from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.api.r_div import divRou

rou = APIRouter()

rou.include_router(divRou)


@rou.get("/")
def rouGet():
    return RedirectResponse(url="http://localhost:5173")
