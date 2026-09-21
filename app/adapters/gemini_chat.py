import logging

from google.genai import types

from app.adapters.gemini import (
    get_gemini_client,
    get_groq_client,
    next_ai_model,
)

logger = logging.getLogger(__name__)


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


async def _call_gemini(model, system_instruction, contents, response_mime_type) -> str:
    resp = await get_gemini_client().aio.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type=response_mime_type,
            temperature=0.2,
        ),
    )
    text = resp.text
    if text:
        return text
    # No usable text. Do NOT return "" — that just trips the caller on an empty
    # parse with no clue why. Surface Gemini's actual reason (safety block,
    # MAX_TOKENS, recitation, ...) so the failure names itself.
    feedback = getattr(resp, "prompt_feedback", None)
    block = getattr(feedback, "block_reason", None)
    candidates = getattr(resp, "candidates", None) or []
    finish = getattr(candidates[0], "finish_reason", None) if candidates else None
    raise RuntimeError(
        f"Gemini {model} returned no text (finish_reason={finish}, block_reason={block})"
    )


async def _call_groq(model, messages, response_mime_type) -> str:
    client = get_groq_client()
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not configured")
    kwargs = {
        "model": model,
        # messages are already role/content dicts (system/user/assistant) -- Groq
        # is OpenAI-compatible so they pass through unchanged.
        "messages": [{"role": m.get("role", "user"), "content": str(m.get("content", ""))} for m in messages],
        "temperature": 0.2,
    }
    if response_mime_type == "application/json":
        kwargs["response_format"] = {"type": "json_object"}
    resp = await client.chat.completions.create(**kwargs)
    if not resp.choices:
        raise RuntimeError(f"Groq {model} returned no choices")
    content = resp.choices[0].message.content
    if not content:
        finish = getattr(resp.choices[0], "finish_reason", None)
        raise RuntimeError(f"Groq {model} returned empty content (finish_reason={finish})")
    return content


async def _invoke(provider, model_id, system_instruction, contents, messages, response_mime_type) -> str:
    """Call one model via its provider's client and return raw text output."""
    if provider == "gemini":
        return await _call_gemini(model_id, system_instruction, contents, response_mime_type)
    if provider == "groq":
        return await _call_groq(model_id, messages, response_mime_type)
    raise RuntimeError(f"Unknown AI provider: {provider}")


async def chat_completion_agent_with_model(
    system_prompt: str | list | None = None,
    user_prompt: str | None = None,
    messages: list | None = None,
    model: tuple[str, str] | None = None,
) -> tuple[str, str]:
    """Like chat_completion_agent, but also returns the "provider:model_id" label of
    the model that actually ran, so callers can tell the user exactly which model
    produced the output.

    Hard rotation: uses `model` if the caller already drew one (e.g. to announce it
    first), else draws the next model and advances the global cursor once. There is
    no retry and no in-call fallback. If the model errors or returns no text we log
    the full cause and RE-RAISE -- we never hand back "" for a caller to trip on. The
    cursor has already advanced, so the *next* call naturally uses the next model.
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

    provider, model_id = model or next_ai_model()
    label = f"{provider}:{model_id}"
    try:
        text = await _invoke(provider, model_id, system_instruction, contents, messages, response_mime_type)
    except Exception:
        # Log the full cause, then let it propagate -- swallowing it here is what
        # turned a real Gemini error into a downstream "empty parse" mystery.
        logger.exception("AI %s failed", label)
        raise
    return text, label


async def chat_completion_agent(
    system_prompt: str | list | None = None,
    user_prompt: str | None = None,
    messages: list | None = None,
    model: tuple[str, str] | None = None,
) -> str:
    """
    Gemini/Groq-backed chat helper.
    Supports both repo calling styles:
    - chat_completion_agent(system_prompt, user_prompt)
    - chat_completion_agent(messages=[...])
    """
    text, _ = await chat_completion_agent_with_model(system_prompt, user_prompt, messages, model)
    return text


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


