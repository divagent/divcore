import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


llm = ChatOpenAI(
    model="gpt-5-nano",  # Your Azure deployment name
    base_url="https://haystacked.openai.azure.com/openai/v1/",
    api_key=os.environ["AZURE_OPENAI_API_KEY"]
)

# response = llm.invoke("Hello, how are you?")
# print(response.content)


async def run_chain(question: str) -> str:
    response = await llm.ainvoke([
        SystemMessage(content="You are a helpful assistant that answers clearly in text."),
        HumanMessage(content=question)
    ])
    return response.content