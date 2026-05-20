# app/langchain/executor.py
from .lc_agent import agent
from .lc_tools import TOOLS
from app.core.ai_logging import log_event


async def run_langchain_agent(question: str, trace_id: str):
    result = await agent.invoke({
        "messages": [{"role": "user", "content": question}]
    })
    return result["structured_response"]