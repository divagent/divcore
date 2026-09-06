"""All live HTTP endpoints for the dividend app, in one router.

Two groups, same router:
  - show     : Postgres reads (only /div_show/list is live today)
  - workflow : the Gemini-backed analyze / predict / calendar endpoints
               (labelled "Agent" historically — it is a workflow, not an agent)

Paths are kept identical to the old r_div_show / r_div_agent split so nothing
calling the API needs to change.
"""

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
from app.service.ser_forward_rate import enrich_forward_rates
from app.adapters import gcal_mcp
from app.adapters.gcal_api import CalendarNotConfigured, list_events

divRou = APIRouter()


# --------------------------------------------------------------------------- #
# show — Postgres reads
# --------------------------------------------------------------------------- #
@divRou.get("/div_show/list", tags=["show Calendar"])
async def list_divs(
    back: int = Query(365, ge=0, le=3650, description="Days before today to include"),
    ahead: int = Query(365, ge=0, le=3650, description="Days after today to include"),
):
    """List this app's dividend calendar events over a window around today.

    Data source is the Google Calendar MCP adapter (calendar is the source of
    truth), not Postgres. Defaults to +/- one year; override with `back`/`ahead`.
    Never 500s — a missing/failed calendar comes back as an empty list.
    """
    today = date.today()
    start = today - timedelta(days=back)
    end = today + timedelta(days=ahead)
    trace_id = f"api:div_show_list:{back}:{ahead}"

    try:
        return await gcal_mcp.list_events(
            time_min=start.isoformat(),
            time_max=end.isoformat(),
            trace_id=trace_id,
        )
    except CalendarNotConfigured:
        return []
    except Exception as exc:  # never let the list crash the page
        log_event(
            "div_show_list_failure", trace_id=trace_id, severity="HIGH", error=str(exc)
        )
        return []


# --------------------------------------------------------------------------- #
# workflow — Gemini analyze / predict / calendar
# --------------------------------------------------------------------------- #
@divRou.post("/div_agent/analyze_dividend", response_model=AnalyzeResponse, tags=["Agent"])
async def analyze_dividend_endpoint(req: AnalyzeRequest):
    """Gemini agent read on a single clicked calendar event: pulls live news and
    returns a headline, reliability label, and reasoning (payment history, cadence,
    coverage, confidence). Never 500s — failures come back as a low-signal read."""
    return await analyze_dividend(
        req, trace_id=f"api:analyze:{req.symbol.strip().upper()}"
    )


@divRou.post("/div_agent/predict_dividend", response_model=PredictResponse, tags=["Agent"])
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


@divRou.get("/div_agent/calendar_upcoming", response_model=UpcomingCalendarResponse, tags=["Agent"])
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
        # Forward yield (vs. the latest price — live, or last close when the
        # market's shut) is stamped on each event and cached per-day: the first
        # viewer of the day fetches + writes it back, later viewers reuse it.
        raw = await enrich_forward_rates(raw, trace_id=trace_id)
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
