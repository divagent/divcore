AGENT_SYSTEM_PROMPT = """
You are a decision-making agent for a dividend information system.

Decide whether the user's question requires searching dividend data.

Rules:
- Choose "search" ONLY if answering requires specific dividend records or upcoming dividend events.
- Choose "no_search" if the question is general knowledge or conceptual.
- Respond ONLY in valid JSON.
"""

def build_agent_prompt(question: str) -> str:
    return f"""
User question:
{question}

Respond in JSON with:
- action: "search" or "no_search"
- reason: short explanation
"""
