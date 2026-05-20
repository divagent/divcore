from typing import Any, Sequence

from google.genai import types
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.llm.gemini import DEFAULT_GEMINI_MODEL, get_gemini_client


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    return str(content)


def _split_messages(messages: list[BaseMessage]) -> tuple[str | None, list[types.Content]]:
    system_parts: list[str] = []
    contents: list[types.Content] = []

    for message in messages:
        text = _message_text(message)
        if isinstance(message, SystemMessage):
            system_parts.append(text)
            continue

        role = "model" if isinstance(message, AIMessage) else "user"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
        )

    system_instruction = "\n\n".join(system_parts) if system_parts else None
    return system_instruction, contents


class GeminiChatModel(BaseChatModel):
    model: str = DEFAULT_GEMINI_MODEL
    temperature: float = 0.2

    def _config(self, system_instruction: str | None, **kwargs: Any) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=kwargs.get("temperature", self.temperature),
        )

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_instruction, contents = _split_messages(messages)
        response = get_gemini_client().models.generate_content(
            model=self.model,
            contents=contents,
            config=self._config(system_instruction, **kwargs),
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response.text or ""))])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        system_instruction, contents = _split_messages(messages)
        response = await get_gemini_client().aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=self._config(system_instruction, **kwargs),
        )
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response.text or ""))])

    def bind_tools(
        self,
        tools: Sequence[Any],
        *,
        tool_choice: str | None = None,
        **kwargs: Any,
    ) -> "GeminiChatModel":
        return self

    @property
    def _llm_type(self) -> str:
        return "gemini-chat"
