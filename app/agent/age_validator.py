from app.core.ai_logging import log_event

def validate_agent_response(response: str, trace_id: str) -> str:
    """
    Ensures the final response meets production quality standards.
    """
    failure_phrases = [
        "maximum reasoning steps",
        "I don't know",
        "encountered an issue accessing the data"
    ]
    
    # 1. Detect Failure
    is_failure = any(phrase in response for phrase in failure_phrases)
    
    if is_failure:
        # 2. Trigger a specific 'failure' log event for alerting (PagerDuty/Azure Monitor)
        log_event(
            "agent_reasoning_failure", 
            trace_id=trace_id, 
            severity="HIGH",
            final_output=response
        )
        # 3. Graceful fallback for the end-user
        return "I'm having trouble retrieving that specific dividend insight right now. Please try again or refine your query."

    return response