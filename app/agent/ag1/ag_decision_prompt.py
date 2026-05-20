# app/agent/decision.py
from openai import OpenAI
from app.agent.agent_schema import AgentDecisionSchema

client = OpenAI()

SYSTEM_PROMPT = """
    You are a trading-dividend decision agent.
    Your task is ONLY to decide what action to take.
    Do NOT answer the user.
    Do NOT retrieve data.
    Return strictly valid JSON.
"""

def agent_decide(question: str) -> AgentDecisionSchema:
    response = client.responses.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        response_format=AgentDecisionSchema,
    )

    return response.output_parsed
