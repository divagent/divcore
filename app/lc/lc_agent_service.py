from .lc_agent import agent


def lc_run_agent(user_message: str) -> str:
    result = agent.invoke(
        {
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
    )

    if isinstance(result, dict) and "messages" in result:
        return result["messages"][-1].content

    return str(result)
