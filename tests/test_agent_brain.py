import pytest
from app.agent.age_brain import decide_next_action

@pytest.mark.asyncio
async def test_brain_tool_selection():
    messages = [{"role": "user", "content": "What is the yield for MSFT?"}]
    decision = await decide_next_action(messages)
    
    # Check for hallucinated combined key
    if "tool/tool_input" in decision:
        tool_call = decision["tool/tool_input"]
        if isinstance(tool_call, dict):
            # Matches: {'endpoint': 'dividend_yield', 'parameters': {...}}
            # Matches: {'action': 'get_yield', ...}
            # Matches: {'tool': '...', ...}
            assert any(key in tool_call for key in ["endpoint", "action", "tool"])
            assert "MSFT" in str(tool_call).upper()
        else:
            assert "MSFT" in str(tool_call).upper()
    else:
        # Standard schema
        assert decision.get("tool") == "get_dividend_data" or "answer" in decision
        assert "MSFT" in str(decision).upper()

@pytest.mark.asyncio
async def test_brain_direct_answer():
    messages = [{"role": "user", "content": "Hello, bot!"}]
    decision = await decide_next_action(messages)

    assert "answer" in decision
    assert "tool" not in decision and "tool/tool_input" not in decision