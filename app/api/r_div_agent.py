import asyncio
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.ai_logging import log_event
from app.db.conn.db_async import get_db
from app.schemas.sch_analyze import AnalyzeRequest, AnalyzeResponse
from app.schemas.sch_predict import (
    CalendarItem,
    PredictRequest,
    PredictResponse,
    UpcomingCalendarResponse,
)
from app.service.ser_div_analyze import analyze_dividend
from app.service.ser_div_predict_publish import predict_and_publish
from app.service.ser_gcal_publish import CalendarNotConfigured, list_events

agentRou = APIRouter()


@agentRou.post("/analyze_dividend", response_model=AnalyzeResponse)
async def analyze_dividend_endpoint(req: AnalyzeRequest):
    """Gemini agent read on a single clicked calendar event: pulls live news and
    returns a headline, reliability label, and reasoning (payment history, cadence,
    coverage, confidence). Never 500s — failures come back as a low-signal read."""
    return await analyze_dividend(
        req, trace_id=f"api:analyze:{req.symbol.strip().upper()}"
    )


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


@agentRou.get("/calendar_upcoming", response_model=UpcomingCalendarResponse)
async def calendar_upcoming_endpoint(
    days: int = Query(30, ge=1, le=365, description="Window length in days from today"),
):
    """List this app's published dividend calendar events from today through the
    next `days` days (default 30), sorted by ex-date. If Google Calendar is not
    configured the response is empty with the reason in `errors` (never 500s)."""
    start = date.today()
    end = start + timedelta(days=days)
    trace_id = f"api:calendar_upcoming:{days}"

    try:
        raw = await asyncio.to_thread(
            list_events,
            time_min=start.isoformat(),
            time_max=end.isoformat(),
            trace_id=trace_id,
        )
        items = [CalendarItem(**item) for item in raw]
        return UpcomingCalendarResponse(
            startDate=start.isoformat(), endDate=end.isoformat(), items=items
        )
    except CalendarNotConfigured as exc:
        return UpcomingCalendarResponse(
            startDate=start.isoformat(), endDate=end.isoformat(), errors=[str(exc)]
        )
    except Exception as exc:  # never let the upcoming list crash the page
        log_event(
            "calendar_upcoming_failure", trace_id=trace_id, severity="HIGH", error=str(exc)
        )
        return UpcomingCalendarResponse(
            startDate=start.isoformat(), endDate=end.isoformat(), errors=[str(exc)]
        )