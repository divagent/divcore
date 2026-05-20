# app/agent/decision.py
import json

from google.genai import types

from app.agent.agent_schema import AgentDecisionSchema
from app.llm.gemini import DEFAULT_GEMINI_MODEL, get_gemini_client


# Original OpenAI setup kept for reference:
# from openai import OpenAI
# client = OpenAI()

SYSTEM_PROMPT = """
    You are a trading-dividend decision agent.
    Your task is ONLY to decide what action to take.
    Do NOT answer the user.
    Do NOT retrieve data.
    Return strictly valid JSON.
"""

def agent_decide(question: str) -> AgentDecisionSchema:
    # Original OpenAI parsed response kept for reference:
    # response = client.responses.parse(
    #     model="gpt-5-nano",
    #     messages=[
    #         {"role": "system", "content": SYSTEM_PROMPT},
    #         {"role": "user", "content": question},
    #     ],
    #     response_format=AgentDecisionSchema,
    # )
    # return response.output_parsed
    response = get_gemini_client().models.generate_content(
        model=DEFAULT_GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=AgentDecisionSchema,
            temperature=0,
        ),
    )
    return AgentDecisionSchema.model_validate(json.loads(response.text or "{}"))
