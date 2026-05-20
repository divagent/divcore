# model.py
from langchain.chat_models import init_chat_model

class ModelProvider:
    def __init__(self, model_name: str = "gpt-5-nano"):
        self._model = init_chat_model(model=model_name)

    def get(self):
        return self._model
