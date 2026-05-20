import json
import time
from app.core.ai_logging import log_event
from app.agent.ag1.agent_prompt import AGENT_SYSTEM_PROMPT, build_agent_prompt
from app.llm.azure_openai_chat import chat_completion_agent

# async def decide_action(question: str) -> dict:
#     resp = await chat_completion(
#         AGENT_SYSTEM_PROMPT,
#         build_agent_prompt(question),
#     )

#     try:
#         return json.loads(resp)
#     except Exception:
#         # hard fallback: always search
#         return {"action": "search", "reason": "failed to parse agent output"}




async def decide_action(question: str) -> dict:
    start = time.perf_counter()
    resp = await chat_completion_agent(
        AGENT_SYSTEM_PROMPT,
        build_agent_prompt(question),
    )
    duration_ms = int((time.perf_counter() - start) * 1000)

    try:
        decision = json.loads(resp)
    except Exception:
        decision = {"action": "search", "reason": "failed to parse agent output"}

    log_event(
        "agent_decision",
        action=decision.get("action"),
        reason=decision.get("reason"),
        latency_ms=duration_ms,
    )

    return decision
