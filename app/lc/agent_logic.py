from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from app.llm.gemini_langchain import GeminiChatModel

@tool
def get_stock_price(ticker: str) -> str:
    """Returns the current price of a stock ticker."""
    return f"The price of {ticker} is $150.00."

def get_agent_chain():
    # Original Azure/OpenAI setup kept for reference:
    # import os
    # from langchain_openai import ChatOpenAI
    # llm = ChatOpenAI(
    #     model="gpt-5-nano",
    #     azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    #     api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    #     api_version="2024-08-01-preview"
    # )
    llm = GeminiChatModel()

    # Bind tools directly to the LLM
    tools = [get_stock_price]
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant with access to tools."),
        ("human", "{input}"),
    ])

    # A simple Runnable chain
    return prompt | llm_with_tools
