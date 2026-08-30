# Follow-up: Google Calendar OAuth prerequisites (do tomorrow)

Goal: produce the four things the backend needs to publish predicted dividends to a
public Google Calendar — a **client ID**, **client secret**, a **refresh token**
(minted as the calendar-owning account, offline), and the **calendar ID**.

Env var names below match our `pydantic-settings` style so they drop straight into `.env`.

---

## STATUS (updated 2026-08-30)

Done in code / env (no browser needed):
- ✅ Config: all four fields on `app/config.py::_Settings` + placeholders in `.env.example`.
- ✅ `.env` has `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`.
- ✅ Mint script: `scripts/mint_refresh_token.py` (Part E) ready to run.
- ✅ **Section 3 built**: `app/service/ser_gcal_publish.py` — `GoogleCalendarClient` /
  `publish_prediction()` turns a `DividendPrediction` into an idempotent all-day event
  via the REST path. Offline logic unit-checked (event shaping, valid id, config guards).
- ✅ Deps synced: `azure-search-documents` + `google-api-python-client` installed
  (predictor chain now imports; the "Also outstanding" blocker below is resolved).

- ✅ **Part D**: public "Predicted Dividends" calendar created; `GOOGLE_CALENDAR_ID` in `.env`.
- ✅ **Part E**: OAuth app PUBLISHED (Production → long-lived token); refresh token minted as
  `dividendagents@gmail.com` and stored as `GOOGLE_OAUTH_REFRESH_TOKEN` in `.env`.
  (mint script now falls back to `.env` via settings + fixes its own sys.path.)
- ✅ **Part G**: verified end-to-end 2026-08-30 — created a real event, confirmed idempotent
  update on rerun (same event id), then deleted the TEST event. **All four creds work.**

Nothing left here — the calendar path is live. Remaining work is product wiring
(batch predict → publish), not OAuth.

---

## Part A — Google Cloud project + enable APIs

1. https://console.cloud.google.com — sign in as the account that will **own the shared
   public calendar** (the refresh token is bound to this account).
2. Create/select a project (top bar → project dropdown → **New Project**). Note the project ID.
3. Enable the APIs (console: APIs & Services → Library → search & **Enable**), or via gcloud:

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable calendar-json.googleapis.com
gcloud services enable calendarmcp.googleapis.com   # only if using the preview MCP endpoint
```

- `calendar-json.googleapis.com` — the one that matters for the reliable REST fallback.
- `calendarmcp.googleapis.com` — Developer-Preview MCP endpoint (may be gated).

---

## Part B — OAuth consent screen

1. **APIs & Services → OAuth consent screen**.
2. User type: **External** (Internal only if everyone is in one Workspace org).
3. Fill app name, support email, developer email. Save.
4. **Scopes** → Add scope:
   - `https://www.googleapis.com/auth/calendar.events` (create/update events — all we need).
5. **Test users** → add the calendar-owning account.
   - In "Testing" mode, test-user refresh tokens may expire after ~7 days.
   - **Click "Publish app" (Production)** to get a long-lived refresh token (recommended for
     a hands-off calendar).

---

## Part C — Create the OAuth 2.0 client (id + secret)

1. **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. Application type: **Web application**.
3. Authorized redirect URIs → add: `http://localhost:8765/`
   (only used by the one-time local consent script below; never needs to be public).
4. Create → copy the **Client ID** and **Client secret**.

---

## Part D — The public calendar + its ID

1. https://calendar.google.com as the owner account.
2. Left sidebar → **Other calendars → +** → **Create new calendar** (e.g. "Predicted Dividends"). Create.
3. Calendar Settings → **Access permissions for events** → check **Make available to public**
   → "See all event details".
4. Same page → **Integrate calendar** → copy the **Calendar ID**
   (looks like `...@group.calendar.google.com`). Also grab the **Public URL / subscribe link**
   here for the frontend's "Add to calendar" button.

---

## Part E — Mint the refresh token (one-time, offline)

Reliable path: a tiny local script run **once** as the owner account.

```bash
pip install google-auth-oauthlib
```

Save as `scripts/mint_refresh_token.py` and run:

```python
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_CONFIG = {
    "web": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8765/"],
    }
}
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, scopes=SCOPES)
# access_type=offline + prompt=consent forces Google to return a refresh_token
creds = flow.run_local_server(port=8765, access_type="offline", prompt="consent")
print("\nREFRESH TOKEN:\n", creds.refresh_token)
```

Opens a browser → **sign in as the calendar owner** → grant access → terminal prints the
**refresh token**. Copy it.

> Alternative (no script): [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
> → gear icon → "Use your own OAuth credentials" → paste client id/secret → authorize
> `calendar.events` → "Exchange authorization code for tokens" → copy the refresh token.
> (Requires adding `https://developers.google.com/oauthplayground` as a redirect URI in Part C.)

---

## Part F — Store the secrets in the backend

Add to `.env` (never commit; never send to the frontend):

```bash
GOOGLE_OAUTH_CLIENT_ID="....apps.googleusercontent.com"
GOOGLE_OAUTH_CLIENT_SECRET="...."
GOOGLE_OAUTH_REFRESH_TOKEN="1//0...."
GOOGLE_CALENDAR_ID="....@group.calendar.google.com"
```

When Section 3 is built, these four fields get added to `app/config.py::_Settings` and to
`.env.example` (placeholders), read via `get_settings_singleton()`.

---

## Part G — Quick verification (optional)

Confirms the refresh token actually creates an event:

```bash
pip install google-api-python-client google-auth
```

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials(
    None,
    refresh_token="YOUR_REFRESH_TOKEN",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    token_uri="https://oauth2.googleapis.com/token",
    scopes=["https://www.googleapis.com/auth/calendar.events"],
)
svc = build("calendar", "v3", credentials=creds)
ev = svc.events().insert(calendarId="YOUR_CALENDAR_ID", body={
    "summary": "TEST Div ~$1.66 (predicted ↑)",
    "start": {"date": "2026-09-10"},
    "end":   {"date": "2026-09-11"},
}).execute()
print("Created:", ev["id"], ev.get("htmlLink"))
```

If it prints a created event id, all four credentials are correct and the backend can
publish headlessly.

---

## Notes (tie-in to plan risk section)

- Scoped to `calendar.events` + the **direct REST API path** — the robust, documented way to
  write headlessly. The preview MCP endpoint (`calendarmcp.googleapis.com`) currently targets
  interactive hosts and lists mostly read scopes; the same refresh token feeds either
  transport, so REST is the safe default behind the `GoogleCalendarMcpClient` interface.
- Default to **all-day** events (`start.date`/`end.date`) — reads best on a subscribed phone
  for an ex-date.

---

## Also outstanding (separate from OAuth)

- ✅ RESOLVED (2026-08-30): `uv sync` installed `azure-search-documents[aio]`; the agent
  tool chain (`age_tools` → `ser_ai_rag` → `ser_div_az_search`) and `age_predictor` now
  import cleanly in the venv. Also added/installed `google-api-python-client` for the
  calendar publishing client.
  - NOTE: use `uv run python ...` (the `.venv`), not the bare system `python`.
