import json
import time  # Changed from 'from time import time' to 'import time'
import uuid
from app.agent.ag1.agent_loop import run_agent_loop
from app.core.ai_logging import log_event
from app.llm.azure_openai_chat import chat_completion_agent
from app.service.ser_ai_rag import rag_query

async def run_agent_executor(question: str):
    trace_id = f"tr-{uuid.uuid4().hex[:8]}" 
    start_perf = time.perf_counter() # Production-standard for latency
    
    log_event("agent_request_received", trace_id=trace_id, question=question)

    # 1. Brain Decision
    decision = await run_agent_loop(question)
    log_event("agent_decision", trace_id=trace_id, decision=decision)
    
    # 2. Tool Execution Logic
    if "tool" in decision and decision["tool"] == "get_dividend_data":
        tool_input = decision.get("tool_input", question)
        
        # Call your existing RAG
        rag_result = await rag_query(question=tool_input, top_k=3)
        
        log_event("tool_completion", trace_id=trace_id, tool="get_dividend_data")

        # 3. Final Synthesis (The "Final Polish")
        final_prompt = f"""
        The user asked: {question}
        Based on the retrieval tool, we found this data: {rag_result.get('answer')}
        Sources used: {rag_result.get('sources')}
        
        Provide a concise final answer to the user.
        """
        
        final_answer = await chat_completion_agent(
            system_prompt="You are a helpful financial assistant.",
            user_prompt=final_prompt
        )
        
        total_latency = int((time.perf_counter() - start_perf) * 1000)
        log_event("agent_request_finished", trace_id=trace_id, latency_ms=total_latency)

        return {
            "answer": final_answer,
            "trace_id": trace_id,
            "intermediate_steps": decision,
            "raw_rag_data": rag_result
        }

    # 4. Handle Direct Answer (Greetings, etc.)
    total_latency = int((time.perf_counter() - start_perf) * 1000)
    log_event("agent_request_finished", trace_id=trace_id, latency_ms=total_latency)
    
    return {
        "answer": decision.get("answer"), 
        "trace_id": trace_id,
        "intermediate_steps": decision
    }