from google.genai import types

from app.llm.gemini import DEFAULT_GEMINI_MODEL, get_gemini_client


# Original Azure/OpenAI setup kept for reference:
# import os
# from openai import AzureOpenAI, AsyncOpenAI
# from app.config import get_settings_singleton
#
# settings = get_settings_singleton()
# subscription_key=settings.OPENAI_API_KEY,
# endpoint = "https://haystacked.cognitiveservices.azure.com/"
# model_name = "gpt-5-nano"
# deployment = "gpt-5-nano"
# api_version = "2024-12-01-preview"
# client = AsyncOpenAI(
#     api_key=settings.OPENAI_API_KEY,
#     base_url="https://haystacked.openai.azure.com/openai/v1/",
# )

deployment = DEFAULT_GEMINI_MODEL


def _wants_json(system_prompt: str | None, messages: list | None) -> bool:
    text = system_prompt or ""
    if messages:
        text += "\n".join(str(m.get("content", "")) for m in messages)
    return "json" in text.lower()


def _gemini_contents(messages: list) -> tuple[str | None, list[types.Content]]:
    system_parts: list[str] = []
    contents: list[types.Content] = []

    for message in messages:
        role = message.get("role")
        content = str(message.get("content", ""))
        if role == "system":
            system_parts.append(content)
            continue

        gemini_role = "model" if role == "assistant" else "user"
        contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=content)],
            )
        )

    return "\n\n".join(system_parts) if system_parts else None, contents


async def chat_completion_agent(
    system_prompt: str | list | None = None,
    user_prompt: str | None = None,
    messages: list | None = None,
) -> str:
    """
    Gemini-backed replacement for the old Azure/OpenAI helper.
    Supports both repo calling styles:
    - chat_completion_agent(system_prompt, user_prompt)
    - chat_completion_agent(messages=[...])
    """
    if messages is None and isinstance(system_prompt, list):
        messages = system_prompt
        system_prompt = None

    if messages is None:
        messages = [
            {"role": "system", "content": system_prompt or ""},
            {"role": "user", "content": user_prompt or ""},
        ]

    system_instruction, contents = _gemini_contents(messages)
    response_mime_type = "application/json" if _wants_json(str(system_prompt or ""), messages) else None

    resp = await get_gemini_client().aio.models.generate_content(
        model=deployment,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type=response_mime_type,
            temperature=0.2,
        ),
    )
    return resp.text or ""


# async def chat_completion(system_prompt: str, user_prompt: str) -> str:
#     resp = await client.chat.completions.create(
#         model=model_name,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt},
#         ],
#         temperature=0.2,
#     )
#     return resp.choices[0].message.content


# response = client.chat.completions.create(
#     messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful assistant.",
#         },
#         {
#             "role": "user",
#             "content": "I am going to Paris, what should I see?",
#         }
#     ],
#     max_completion_tokens=16384,
#     model=deployment
# )

# print(response.choices[0].message.content)


