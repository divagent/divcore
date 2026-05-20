import json

from google.genai import types

from app.llm.gemini import DEFAULT_GEMINI_MODEL, get_gemini_client


# Original Azure/OpenAI setup kept for reference:
# import os
# from openai import AsyncOpenAI
# deployment = "gpt-5-nano"
# client = AsyncOpenAI(
#     api_key=os.environ["AZURE_OPENAI_API_KEY"],
#     base_url="https://haystacked.openai.azure.com/openai/v1/",
# )
deployment = DEFAULT_GEMINI_MODEL

AGENT_SYSTEM_PROMPT = """
You are a Financial Data Agent. You have access to a tool called 'get_dividend_data'.
Use this tool ONLY when the user asks about dividends, yields, or payouts.
For general greetings or non-financial questions, answer directly.

You MUST respond in valid JSON format.

If you need to look up data, respond:
{
    "thought": "Reasoning why you need to search dividends",
    "tool": "get_dividend_data",
    "tool_input": "the specific stock or query to search"
}

If you can answer without a tool (e.g., greetings), respond:
{
    "thought": "No search needed for a greeting",
    "answer": "Your direct response here"
}
"""

async def run_agent_loop(question: str):
    # The LLM "Reasoning" call
    resp = await get_gemini_client().aio.models.generate_content(
        model=deployment,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=AGENT_SYSTEM_PROMPT,
            response_mime_type="application/json",
            temperature=0,
        ),
    )
    
    # Parse the brain's decision
    decision = json.loads(resp.text or "{}")
    return decision
