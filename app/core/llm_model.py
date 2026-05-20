from app.llm.gemini_langchain import GeminiChatModel


def get_model_lc_azopenai() -> GeminiChatModel:
    # Original Azure/OpenAI model kept for reference:
    # import os
    # from langchain_openai import ChatOpenAI
    # return ChatOpenAI(
    #     model="gpt-5-nano",
    #     base_url="https://haystacked.openai.azure.com/openai/v1/",
    #     api_key=os.environ["AZURE_OPENAI_API_KEY"],
    #     max_completion_tokens=1000,
    #     timeout=30,
    # )
    return GeminiChatModel()
