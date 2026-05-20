from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .lc_wrapper import AzureChat

llm = AzureChat()

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a financial assistant specialized in dividend data."),
    ("human", "{question}")
])

chain = prompt | llm | StrOutputParser()

async def run_chain(question: str) -> str:
    return await chain.ainvoke({"question": question})
