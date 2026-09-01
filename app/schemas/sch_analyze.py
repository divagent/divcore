"""Wire schemas for POST /div_agent/analyze_dividend.

Drives the "Agent analysis" panel in the frontend: the user clicks a row in the
upcoming-dividend calendar and the right-hand panel shows a Gemini-generated
read on that specific dividend event (reliability, cadence, and the reasoning
behind the ex-date). camelCase on purpose — matches the JSON the browser sends.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---- Request -------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    symbol: str
    exDate: Optional[str] = None          # ISO yyyy-mm-dd of the clicked event
    amount: Optional[float] = None        # per-share amount, if known
    kind: Literal["fact", "estimate", "prediction"] = "fact"
    confidence: Optional[float] = None    # 0..1, for prediction rows
    summary: Optional[str] = None         # the calendar row's own summary text


# ---- Response ------------------------------------------------------------


class AnalysisSource(BaseModel):
    title: str = ""
    url: str


class AnalyzeResponse(BaseModel):
    symbol: str
    exDate: Optional[str] = None
    # One-line takeaway shown as the panel headline.
    headline: str = ""
    # The main body: payment history, cadence stability, coverage, and the
    # confidence behind this ex-date. Plain text / light markdown.
    reasoning: str = ""
    # Coarse reliability read the UI can color-code.
    riskLabel: Literal["low", "medium", "high", "unknown"] = "unknown"
    sources: List[AnalysisSource] = Field(default_factory=list)
    model: Optional[str] = None
    generatedAt: Optional[str] = None
