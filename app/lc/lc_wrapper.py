from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from typing import List
from openai import AsyncOpenAI
import os

_client = AsyncOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    base_url="https://haystacked.openai.azure.com/openai/v1/",
)

class AzureChat(BaseChatModel):
    model: str = "gpt-5-nano"

    async def _agenerate(self, messages, **kwargs):
        resp = await _client.chat.completions.create(
            model=self.model,
            messages=[m.dict() for m in messages],
        )
        return AIMessage(content=resp.choices[0].message.content)

    @property
    def _llm_type(self) -> str:
        return "azure-openai-chat"
