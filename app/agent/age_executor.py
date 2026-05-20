import json
from app.agent.age_brain import decide_next_action
from app.agent.age_tools import get_dividend_data_tool, search_web_tool
from app.core.ai_logging import log_event

# 1. Structural Validator (Defined locally or imported)
def normalize_decision(decision: dict) -> dict:
    if "tool/tool_input" in decision:
        val = decision["tool/tool_input"]
        if isinstance(val, dict):
            decision["tool"] = val.get("tool") or val.get("action") or val.get("endpoint")
            decision["tool_input"] = str(val.get("input") or val.get("parameters") or val.get("ticker") or "")
    return decision

# 2. Quality Validator (The one you shared)
def validate_agent_response(response: str, trace_id: str) -> str:
    failure_phrases = ["maximum reasoning steps", "I don't know", "encountered an issue"]
    if any(phrase in response for phrase in failure_phrases):
        log_event("agent_reasoning_failure", trace_id=trace_id, severity="HIGH")
        return "I'm having trouble retrieving that dividend insight right now."
    return response

async def run_agent_executor(question: str, trace_id: str):
    messages = [{"role": "user", "content": question}]
    max_turns = 3 
    final_output = "I reached the maximum reasoning steps without a clear answer."
    
    for turn in range(max_turns):
        # THINK
        raw_decision = await decide_next_action(messages)
        
        # USE STRUCTURAL VALIDATOR HERE
        decision = normalize_decision(raw_decision)
        
        log_event("agent_thought", trace_id=trace_id, turn=turn, decision=decision)

        # FINISH
        if "answer" in decision:
            final_output = decision["answer"]
            break # Exit loop once we have an answer

        # ACT
        if decision.get("tool") == "get_dividend_data":
            tool_result = await get_dividend_data_tool(decision["tool_input"])
        elif decision.get("tool") == "search_web": # <-- NEW TOOL ADDED HERE
            tool_result = await search_web_tool(decision["tool_input"])
            
        messages.append({"role": "assistant", "content": json.dumps(decision)})
        messages.append({"role": "system", "content": f"Observation: {json.dumps(tool_result)}"})
        log_event("tool_observation", trace_id=trace_id, turn=turn, success="error" not in tool_result)
        

    # USE QUALITY VALIDATOR HERE (Before returning to user)
    return validate_agent_response(final_output, trace_id)