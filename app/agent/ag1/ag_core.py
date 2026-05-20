# app/agent/agent_core.py
from typing import Dict, Any, List
from datetime import date, timedelta

# from app.agent.ag_service import run_rag  # your existing RAG
from app.core.ai_logging import logger  # your existing logger

CONFIDENCE_THRESHOLD = 0.6

async def run_agent(question: str) -> Dict[str, Any]:
    logger.info("agent.start", extra={"question": question})

    # ---- Step 1: Simple, testable intent gate (NO LLM) ----
    q = question.lower()
    if "buy" in q or "sell" in q or "hold" in q:
        intent = "trading_decision"
    elif "dividend" in q:
        intent = "dividend_knowledge"
    else:
        return {
            "status": "REFUSED",
            "reason": "Unsupported intent"
        }

    logger.info("agent.intent", extra={"intent": intent})

    # ---- Step 2: Call your existing RAG (unchanged) ----
    rag_result = "await run_rag(question)"
    # EXPECTED rag_result:
    # {
    #   "answer": "...",
    #   "confidence": float,
    #   "sources": [...]
    # }

    logger.info("agent.rag_result", extra=rag_result)

    # ---- Step 3: Agent gate (THIS is new) ----
    if not rag_result.get("sources"):
        return {
            "status": "NO_DECISION",
            "reason": "No supporting dividend data found",
            "sources": []
        }

    if rag_result.get("confidence", 0.0) < CONFIDENCE_THRESHOLD:
        return {
            "status": "LOW_CONFIDENCE",
            "confidence": rag_result.get("confidence"),
            "sources": rag_result.get("sources")
        }

    # ---- Step 4: Final decision ----
    return {
        "status": "DECISION",
        "decision": rag_result["answer"],
        "confidence": rag_result["confidence"],
        "sources": rag_result["sources"]
    }
