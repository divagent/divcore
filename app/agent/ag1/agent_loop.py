import json
import os
from openai import AsyncOpenAI

# Production Config from your snippet
deployment = "gpt-5-nano"
client = AsyncOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    base_url="https://haystacked.openai.azure.com/openai/v1/",
)

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
    resp = await client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        response_format={"type": "json_object"} # Ensures valid JSON for the parser
    )
    
    # Parse the brain's decision
    decision = json.loads(resp.choices[0].message.content)
    return decision