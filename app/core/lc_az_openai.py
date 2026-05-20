from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os

AZURE_OPENAI_ENDPOINT = "https://haystacked.cognitiveservices.azure.com/"
AZURE_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]

llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    azure_deployment="gpt-5-nano",
    api_version="2024-12-01-preview",
    api_key=AZURE_API_KEY,
    max_tokens=1500,
)

async def run_chain(question: str) -> str:
    response = await llm.ainvoke([
        SystemMessage(content="You are a helpful assistant that answers clearly in text."),
        HumanMessage(content=question)
    ])
    return response.content