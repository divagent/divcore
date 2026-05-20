import json
from app.agent.agent_schema import AgentDecision
from app.llm.azure_openai_chat import chat_completion_agent


async def decide_next_action(messages: list) -> AgentDecision:
    """
    Refined reasoning unit for Multi-Tool routing (RAG vs. Web Search).
    """

    # Updated System Prompt with specific tool instructions
    system_message_content = (
        "You are an Elite Financial Dividend Agent. Respond ONLY in JSON with 'thought' and "
        "either 'tool/tool_input' or 'answer'.\n\n"
        "TOOLS AVAILABLE:\n"
        "1. get_dividend_data: Accesses our internal high-fidelity database for dividend yields, "
        "payout ratios, and historical filings. Use this as your primary source for hard facts.\n"
        "2. search_web: Searches the live internet for recent news, market sentiment, macro-economic "
        "trends, or events after your knowledge cutoff.\n\n"
        "STRATEGY:\n"
        "- If the user asks for yield or specific dividend history, use 'get_dividend_data'.\n"
        "- If the user asks for 'recent news', 'why the stock is down', or 'sentiment', use 'search_web'.\n"
        "- You have 3 turns. Synthesize the final answer once you have sufficient data."
    )

    system_message = {"role": "system", "content": system_message_content}

    # 1. Ensure the System Message is always at the top
    if not messages or messages[0]["role"] != "system":
        messages.insert(0, system_message)
    else:
        # Update it in case we changed the instructions
        messages[0] = system_message

    # 2. Critical Production Fix: Pass FULL messages for context-aware reasoning
    # This allows the model to 'see' the RAG observations from previous turns.
    response_text = await chat_completion_agent(
        messages=messages  # Changed from separate prompts to full list
    )

    try:
        # Ensure it's clean JSON
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Fallback if the model outputs raw text
        return {"thought": "Parsing response as raw text.", "answer": response_text}


