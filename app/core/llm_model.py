import os
from langchain_openai import ChatOpenAI


def get_model_lc_azopenai() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-5-nano",
        base_url="https://haystacked.openai.azure.com/openai/v1/",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        max_completion_tokens=1000,
        timeout=30,
    )
