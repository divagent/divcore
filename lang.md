| Old LangChain term | LangGraph term                 | What it really is   |
| ------------------ | ------------------------------ | ------------------- |
| Agent              | **Graph**                      | The whole system    |
| Agent loop         | **Cycle in graph**             | ReAct loop          |
| Agent step         | **Node**                       | One decision/action |
| Agent memory       | **State**                      | Typed state object  |
| Tool               | **Node (tool node)**           | Tool call           |
| AgentExecutor      | **Compiled graph**             | Runtime             |
| Intermediate steps | **State fields**               | Scratchpad          |
| Multi-agent        | **Multiple nodes / subgraphs** | Explicit            |
