from langchain.agents import create_agent

from app.core.llm_model import get_model_lc_azopenai
from .lc_tools import TOOLS, handle_tool_errors


def create_lc_agent():
    return create_agent(
        model=get_model_lc_azopenai(),
        tools=TOOLS,
        middleware=[handle_tool_errors],
        system_prompt="You are a helpful assistant. Be concise and accurate.",
    )


# Singleton agent
agent = create_lc_agent()
