import time
from app.core.ai_logging import log_event
from app.service.ser_div_az_search import search_dividends
from app.core.rag_prompt import SYSTEM_PROMPT, build_user_prompt
from app.llm.azure_openai_chat import chat_completion_agent
from .ser_ai_agent import decide_action

async def rag_query_contract(question: str, top_k: int):
    chunks = await search_dividends(question, top_k)

    if not chunks:
        return {
            "answer": "I don't have enough dividend data to answer this question.",
            "sources": [],
            "meta": {"retrieved_chunks": 0},
        }

    contexts = [c["content"] for c in chunks]

    user_prompt = build_user_prompt(question, contexts)
    answer = await chat_completion_agent(SYSTEM_PROMPT, user_prompt)

    return {
        "answer": answer,
        "sources": chunks,
        "meta": {
            "retrieved_chunks": len(chunks),
        },
    }




async def rag_query(question: str, top_k: int):
    decision = await decide_action(question)

    if decision["action"] == "no_search":
        return {
            "answer": "This question does not require dividend data lookup.",
            "sources": [],
            "meta": {
                "agent_decision": decision,
                "retrieved_chunks": 0,
            },
        }

    # otherwise: search
    # chunks = await search_dividends(question, top_k)
    search_start = time.perf_counter()
    chunks = await search_dividends(question, top_k)
    search_ms = int((time.perf_counter() - search_start) * 1000)

    log_event(
        "search_completed",
        retrieved_chunks=len(chunks),
        latency_ms=search_ms,
    )


    if not chunks:
        return {
            "answer": "I don't have enough dividend data to answer this question.",
            "sources": [],
            "meta": {
                "agent_decision": decision,
                "retrieved_chunks": 0,
            },
        }

    contexts = [c["content"] for c in chunks]
    user_prompt = build_user_prompt(question, contexts)
    # answer = await chat_completion(SYSTEM_PROMPT, user_prompt)
    llm_start = time.perf_counter()
    answer = await chat_completion_agent(SYSTEM_PROMPT, user_prompt)
    llm_ms = int((time.perf_counter() - llm_start) * 1000)

    log_event(
        "llm_completed",
        model="gpt-5-nano",
        latency_ms=llm_ms,
    )


    return {
        "answer": answer,
        "sources": chunks,
        "meta": {
            "agent_decision": decision,
            "retrieved_chunks": len(chunks),
        },
    }
