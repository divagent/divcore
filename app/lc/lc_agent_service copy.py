import os

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


model = ChatOpenAI(
    model="gpt-5-nano",  # Your Azure deployment name
    base_url="https://haystacked.openai.azure.com/openai/v1/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    max_completion_tokens=1000,
    timeout=30,
)


# # ---- Model ----
# model = ChatOpenAI(
#     model="gpt-5-nano",
#     max_tokens=1000,
#     timeout=30,
# )


# ---- Tools ----
@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"


@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"


# ---- Middleware ----
@wrap_tool_call
def handle_tool_errors(request, handler):
    try:
        return handler(request)
    except Exception as e:
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"],
        )


# ---- Agent (singleton) ----
agent = create_agent(
    model=model,
    tools=[search, get_weather],
    middleware=[handle_tool_errors],
    system_prompt="You are a helpful assistant. Be concise and accurate.",
)


# ---- Public API for FastAPI ----
def lc_run_agent(user_message: str) -> str:
    """
    Execute the agent and return final text output.
    """
    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
    )

    # Most LangChain agents return messages; normalize here
    if isinstance(result, dict) and "messages" in result:
        return result["messages"][-1].content

    return str(result)
