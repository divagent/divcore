# model.py
from app.llm.gemini_langchain import GeminiChatModel

class ModelProvider:
    def __init__(self, model_name: str | None = None):
        # Original generic LangChain initializer kept for reference:
        # from langchain.chat_models import init_chat_model
        # self._model = init_chat_model(model=model_name)
        self._model = GeminiChatModel()

    def get(self):
        return self._model
