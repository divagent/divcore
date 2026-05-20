SYSTEM_PROMPT = """
You are a financial assistant specializing in dividend analysis.

Rules:
- Answer ONLY using the provided context.
- If the context does not contain enough information, say:
  "I don't have enough dividend data to answer this question."
- Do NOT use prior knowledge.
- Be concise and factual.
"""

def build_user_prompt(question: str, contexts: list[str]) -> str:
    joined = "\n\n".join(
        [f"[CONTEXT {i+1}]\n{c}" for i, c in enumerate(contexts)]
    )
    return f"""
Question:
{question}

Context:
{joined}

Answer:
"""
