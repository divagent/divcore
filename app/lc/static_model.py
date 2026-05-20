# from langchain.agents import create_agent
# agent = create_agent("openai:gpt-5-nano", tools=tools)
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-5-nano",
    max_tokens=1000,
    timeout=30
)


@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    return f"Weather in {location}: Sunny, 72°F"

agent = create_agent(model, tools=[search, get_weather])



@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )

agent = create_agent(
    model=model,
    tools=[search, get_weather],
    middleware=[handle_tool_errors],
    system_prompt="You are a helpful assistant. Be concise and accurate."
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)