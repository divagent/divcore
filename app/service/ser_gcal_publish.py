"""Publish predicted dividends to the public Google Calendar.

This is "Section 3" from `followup.md`: it turns a `DividendPrediction` into an
all-day event on the calendar-owning account's public calendar, headlessly, using
a long-lived OAuth **refresh token** (no interactive consent at runtime).

Transport note: we use the documented **REST** path (`calendar.events`) via
`google-api-python-client`. The preview MCP endpoint (`calendarmcp.googleapis.com`)
would sit behind this same interface and consume the same refresh token, so REST is
the safe default. Keep the public surface (`publish_prediction`) transport-agnostic.

Config (all from `get_settings_singleton()`, sourced from `.env` — see followup.md):
    GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET,
    GOOGLE_OAUTH_REFRESH_TOKEN, GOOGLE_CALENDAR_ID

Design decisions carried from the plan:
  * All-day events (`start.date`/`end.date`) — reads best on a subscribed phone.
  * Idempotent: the event id is derived from (symbol, ex-date), so re-running the
    predictor UPDATES the same event instead of creating duplicates.
  * A LOW-confidence prediction is still published (never dropped), tagged in the
    title/description so subscribers can weight it.
"""

from __future__ import annotations

import hashlib
from datetime import date, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.agent.agent_schema import DividendPrediction
from app.config import get_settings_singleton
from app.core.ai_logging import log_event

# Only the scope needed to create/update events on a calendar we own.
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
TOKEN_URI = "https://oauth2.googleapis.com/token"

_DIRECTION_ARROW = {"up": "↑", "down": "↓", "constant": "→"}


class CalendarNotConfigured(RuntimeError):
    """Raised when the four Google credentials are not all present in settings."""


class GoogleCalendarClient:
    """Thin, reusable client that publishes predictions to one Google Calendar.

    Instantiate once and reuse; the underlying `googleapiclient` service (and the
    access token minted from the refresh token) are built lazily and cached.
    """

    def __init__(
        self,
        *,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
        calendar_id: Optional[str] = None,
    ) -> None:
        s = get_settings_singleton()
        self._client_id = client_id or s.GOOGLE_OAUTH_CLIENT_ID
        self._client_secret = client_secret or s.GOOGLE_OAUTH_CLIENT_SECRET
        self._refresh_token = refresh_token or s.GOOGLE_OAUTH_REFRESH_TOKEN
        self._calendar_id = calendar_id or s.GOOGLE_CALENDAR_ID
        self._service = None  # lazy

    # -- configuration ----------------------------------------------------

    @property
    def is_configured(self) -> bool:
        """True only when all four credentials are present."""
        return all(
            (self._client_id, self._client_secret, self._refresh_token, self._calendar_id)
        )

    def _require_config(self) -> None:
        if not self.is_configured:
            missing = [
                name
                for name, val in (
                    ("GOOGLE_OAUTH_CLIENT_ID", self._client_id),
                    ("GOOGLE_OAUTH_CLIENT_SECRET", self._client_secret),
                    ("GOOGLE_OAUTH_REFRESH_TOKEN", self._refresh_token),
                    ("GOOGLE_CALENDAR_ID", self._calendar_id),
                )
                if not val
            ]
            raise CalendarNotConfigured(
                "Google Calendar publishing is not configured; missing: "
                + ", ".join(missing)
                + ". See followup.md (Parts D & E) to mint the refresh token and "
                "grab the calendar id."
            )

    def _get_service(self):
        if self._service is None:
            self._require_config()
            creds = Credentials(
                token=None,
                refresh_token=self._refresh_token,
                client_id=self._client_id,
                client_secret=self._client_secret,
                token_uri=TOKEN_URI,
                scopes=SCOPES,
            )
            # cache_discovery=False avoids a noisy warning + file cache on serverless.
            self._service = build(
                "calendar", "v3", credentials=creds, cache_discovery=False
            )
        return self._service

    # -- event shaping ----------------------------------------------------

    @staticmethod
    def _event_id(symbol: str, ex_date: str) -> str:
        """Deterministic, valid Calendar event id from (symbol, ex-date).

        Calendar ids must be base32hex (chars a-v + 0-9), length 5-1024. A sha1 hex
        digest is all 0-9a-f (⊂ a-v), so it satisfies the charset directly.
        """
        digest = hashlib.sha1(f"{symbol}:{ex_date}".encode("utf-8")).hexdigest()
        return f"div{digest}"

    @classmethod
    def _build_event_body(cls, p: DividendPrediction) -> dict:
        ex_date = p.predicted_ex_date
        arrow = _DIRECTION_ARROW.get(p.direction, "→")
        amount = f"~${p.predicted_amount:.2f}" if p.predicted_amount is not None else "amount TBD"
        low = " [LOW confidence]" if p.confidence_label == "low" else ""

        summary = f"{p.symbol} div {amount} ({arrow} {p.direction}){low}"

        description_lines = [
            f"Predicted dividend for {p.symbol}.",
            f"Direction vs. last: {p.direction}",
            f"Confidence: {p.confidence:.0%} ({p.confidence_label})",
            "",
            (p.reasoning or "No reasoning provided.").strip(),
        ]
        if p.sources:
            description_lines += ["", "Sources:"]
            description_lines += [f"  - {src}" for src in p.sources]
        description_lines += [
            "",
            "Predicted by DivCore — not investment advice.",
        ]

        start = date.fromisoformat(ex_date)
        # All-day events use an exclusive end date: single-day event ends next day.
        end = start + timedelta(days=1)

        return {
            "id": cls._event_id(p.symbol, ex_date),
            "summary": summary,
            "description": "\n".join(description_lines),
            "start": {"date": start.isoformat()},
            "end": {"date": end.isoformat()},
            "transparency": "transparent",  # doesn't block the subscriber's free/busy
            "extendedProperties": {
                "private": {
                    "app": "divcore",
                    "kind": "predicted_dividend",
                    "symbol": p.symbol,
                    "direction": p.direction,
                    "confidence": f"{p.confidence:.4f}",
                }
            },
        }

    # -- public API -------------------------------------------------------

    def upsert_event(
        self,
        *,
        symbol: str,
        ex_date: str,
        summary: str,
        description: str,
        kind: str,
        confidence: Optional[float] = None,
        trace_id: str = "internal",
    ) -> dict:
        """Create or update one all-day event, idempotent by (symbol, ex_date).

        Used for all three layers (fact / estimate / prediction). The id keys on
        (symbol, ex_date) only, so re-running overrides the event on that date in
        place — one event per date, as agreed. Returns the Google event resource
        plus an "action" key ('created' | 'updated')."""
        start = date.fromisoformat(ex_date)
        end = start + timedelta(days=1)
        private = {"app": "divcore", "kind": kind, "symbol": symbol}
        if confidence is not None:
            private["confidence"] = f"{confidence:.4f}"

        body = {
            "id": self._event_id(symbol, ex_date),
            "summary": summary,
            "description": description,
            "start": {"date": start.isoformat()},
            "end": {"date": end.isoformat()},
            "transparency": "transparent",
            "extendedProperties": {"private": private},
        }
        event_id = body["id"]
        service = self._get_service()

        try:
            try:
                event = (
                    service.events()
                    .update(calendarId=self._calendar_id, eventId=event_id, body=body)
                    .execute()
                )
                action = "updated"
            except HttpError as exc:
                if exc.resp.status != 404:
                    raise
                event = (
                    service.events()
                    .insert(calendarId=self._calendar_id, body=body)
                    .execute()
                )
                action = "created"
        except HttpError as exc:
            log_event(
                "gcal_upsert_failure",
                trace_id=trace_id,
                symbol=symbol,
                ex_date=ex_date,
                kind=kind,
                severity="HIGH",
                status=getattr(exc.resp, "status", None),
                error=str(exc),
            )
            raise

        event["action"] = action
        log_event(
            "gcal_upsert_done",
            trace_id=trace_id,
            symbol=symbol,
            ex_date=ex_date,
            kind=kind,
            action=action,
            event_id=event.get("id"),
        )
        return event

    def publish_prediction(
        self, prediction: DividendPrediction, *, trace_id: str = "internal"
    ) -> dict:
        """Create or update the calendar event for a prediction. Idempotent by (symbol, ex-date).

        Returns the Google event resource. Raises `CalendarNotConfigured` if creds are
        missing, or `ValueError` if the prediction has no `predicted_ex_date` (an
        all-day event needs a date).
        """
        if not prediction.predicted_ex_date:
            raise ValueError(
                f"Cannot publish {prediction.symbol}: predicted_ex_date is null; "
                "an all-day calendar event requires a date."
            )

        service = self._get_service()
        body = self._build_event_body(prediction)
        event_id = body["id"]

        log_event(
            "gcal_publish_start",
            trace_id=trace_id,
            symbol=prediction.symbol,
            ex_date=prediction.predicted_ex_date,
            event_id=event_id,
        )

        try:
            # update() is idempotent for a known id; if it doesn't exist yet, fall
            # back to insert() with our deterministic id.
            try:
                event = (
                    service.events()
                    .update(calendarId=self._calendar_id, eventId=event_id, body=body)
                    .execute()
                )
                action = "updated"
            except HttpError as exc:
                if exc.resp.status != 404:
                    raise
                event = (
                    service.events()
                    .insert(calendarId=self._calendar_id, body=body)
                    .execute()
                )
                action = "created"
        except HttpError as exc:
            log_event(
                "gcal_publish_failure",
                trace_id=trace_id,
                symbol=prediction.symbol,
                severity="HIGH",
                status=getattr(exc.resp, "status", None),
                error=str(exc),
            )
            raise

        log_event(
            "gcal_publish_done",
            trace_id=trace_id,
            symbol=prediction.symbol,
            action=action,
            event_id=event.get("id"),
            html_link=event.get("htmlLink"),
        )
        return event


# Module-level convenience: build a client from settings and publish one prediction.
def publish_prediction(
    prediction: DividendPrediction, *, trace_id: str = "internal"
) -> dict:
    """Publish a single prediction using credentials from settings/.env."""
    return GoogleCalendarClient().publish_prediction(prediction, trace_id=trace_id)


def upsert_event(
    *,
    symbol: str,
    ex_date: str,
    summary: str,
    description: str,
    kind: str,
    confidence: Optional[float] = None,
    trace_id: str = "internal",
) -> dict:
    """Upsert one labeled all-day event using credentials from settings/.env."""
    return GoogleCalendarClient().upsert_event(
        symbol=symbol,
        ex_date=ex_date,
        summary=summary,
        description=description,
        kind=kind,
        confidence=confidence,
        trace_id=trace_id,
    )
